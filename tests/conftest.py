"""
Shared pytest fixtures and test configuration.

This module provides common fixtures used across all tests including:
- Temporary directories for isolated test environments
- Mock dependencies for services and utilities
- Test images and file utilities
- FastAPI test client with dependency overrides
- Mock ML models to avoid loading actual models
"""

import pytest
import shutil
import uuid
import os
from pathlib import Path
from typing import Dict
from unittest.mock import Mock, patch
from io import BytesIO
from PIL import Image
from fastapi import UploadFile, HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.storage.directories import DirectoryManager
from app.storage.local_storage import LocalImageStorage
from app.media.service import ImageService
from app.editing.domain.dtos import EditResultDTO
from app.editing.service import ImageEditService
from app.vision.detection_service import ObjectDetectionService
from app.dependencies.storage import get_local_image_storage
from app.dependencies.services import (
    get_image_edit_service,
    get_image_service,
    get_object_detection_service,
)


@pytest.fixture
def temp_base_dir(tmp_path: Path) -> Path:
    """Create a temporary base directory for tests."""
    return tmp_path


@pytest.fixture
def temp_directories(temp_base_dir: Path) -> Dict[str, Path]:
    """Create temporary directories for uploaded, edited, and detected images."""
    dirs = {
        "uploaded": temp_base_dir / "uploaded",
        "edited": temp_base_dir / "edited",
        "detected": temp_base_dir / "detected"
    }
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    return dirs


@pytest.fixture
def cleanup_temp_dirs(temp_directories: Dict[str, Path]):
    """Cleanup fixture to remove temporary directories after tests."""
    yield
    for dir_path in temp_directories.values():
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def mock_directory_manager(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock DirectoryManager."""
    mock = Mock(spec=DirectoryManager)
    mock.get_directory.side_effect = lambda folder: temp_directories.get(folder)
    mock.validate_folder.side_effect = lambda folder: folder in temp_directories
    return mock

@pytest.fixture
def mock_image_service(temp_directories: Dict[str, Path], mock_local_storage: Mock) -> Mock:
    """Create a mock ImageService."""
    from app.media.domain.dtos import DeleteImageResultDTO, ImageDTO, OperationStatusDTO, SaveImageResultDTO

    mock = Mock(spec=ImageService)
    mock.local_storage = mock_local_storage

    def get_image_path_side_effect(image_name: str, folder: str = "uploaded") -> Path:
        return temp_directories.get(folder, temp_directories["uploaded"]) / image_name

    mock.get_image_path.side_effect = get_image_path_side_effect

    def build_image_dto(image_path: Path, folder: str) -> ImageDTO:
        with Image.open(image_path) as img:
            return ImageDTO(
                id=image_path.stem,
                filename=image_path.name,
                format=img.format or "JPEG",
                mode=img.mode,
                width=img.width,
                height=img.height,
                size_bytes=os.path.getsize(image_path),
                path=str(image_path),
                url=None,
                folder=folder,
            )

    def get_images_side_effect(
        folder: str = "uploaded",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageDTO]:
        folder_map = {
            "uploaded": [temp_directories["uploaded"]],
            "edited": [temp_directories["edited"]],
            "detected": [temp_directories["detected"]],
            "all": list(temp_directories.values()),
        }
        if folder not in folder_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid folder: {folder}. Valid options: {list(folder_map.keys())}",
            )

        results: list[ImageDTO] = []
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

        for directory in folder_map[folder]:
            if not directory.exists():
                continue
            image_files = [
                path
                for path in directory.rglob("*")
                if path.suffix.lower() in valid_extensions and path.is_file()
            ]
            for image_path in image_files[offset : offset + limit]:
                try:
                    results.append(build_image_dto(image_path, directory.name))
                except (FileNotFoundError, OSError):
                    continue
        return results

    mock.get_images.side_effect = get_images_side_effect

    def get_image_by_filename_side_effect(filename: str, folder: str = "uploaded") -> ImageDTO:
        image_path = temp_directories.get(folder, temp_directories["uploaded"]) / filename
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {folder}")
        try:
            return build_image_dto(image_path, folder)
        except (FileNotFoundError, OSError):
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {folder}")

    mock.get_image_by_filename.side_effect = get_image_by_filename_side_effect

    def delete_image_side_effect(filename: str, folder: str = "uploaded") -> DeleteImageResultDTO:
        image_path = temp_directories.get(folder, temp_directories["uploaded"]) / filename
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {folder} folder")
        deleted_image = build_image_dto(image_path, folder)
        image_path.unlink()
        return DeleteImageResultDTO(
            status="success",
            message=f"Image {filename} deleted from {folder}",
            deleted_image=deleted_image,
        )

    mock.delete_image.side_effect = delete_image_side_effect

    def delete_images_side_effect(folder: str) -> OperationStatusDTO:
        folder_map = {
            "uploaded": [temp_directories["uploaded"]],
            "edited": [temp_directories["edited"]],
            "detected": [temp_directories["detected"]],
            "all": list(temp_directories.values()),
        }
        if folder not in folder_map:
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}")

        deleted_count = 0
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
        for directory in folder_map[folder]:
            if not directory.exists():
                continue
            for image_path in directory.rglob("*"):
                if image_path.suffix.lower() in valid_extensions and image_path.is_file():
                    image_path.unlink()
                    deleted_count += 1
        return OperationStatusDTO(
            status="success",
            message=f"Deleted {deleted_count} images from {folder}",
        )

    mock.delete_images.side_effect = delete_images_side_effect

    def move_image_side_effect(filename: str, source_folder: str, target_folder: str) -> ImageDTO:
        source_path = temp_directories.get(source_folder, temp_directories["uploaded"]) / filename
        target_path = temp_directories.get(target_folder, temp_directories["edited"]) / filename

        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {source_folder}")
        if target_path.exists():
            raise HTTPException(status_code=409, detail=f"Image {filename} already exists in {target_folder}")

        shutil.move(str(source_path), str(target_path))
        return build_image_dto(target_path, target_folder)

    mock.move_image.side_effect = move_image_side_effect

    mock.upload_image.side_effect = (
        lambda file, filename=None, output_format="JPEG": SaveImageResultDTO(
            path=str(temp_directories["uploaded"] / (filename or "test.jpg")),
            image=ImageDTO(
                id="upload-id",
                filename=filename or "test.jpg",
                format=output_format,
                mode="RGB",
                width=100,
                height=100,
                size_bytes=1024,
                path=str(temp_directories["uploaded"] / (filename or "test.jpg")),
                folder="uploaded",
            ),
        )
    )
    return mock


@pytest.fixture
def mock_local_storage(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock LocalImageStorage."""
    mock = Mock(spec=LocalImageStorage)
    
    def save_side_effect(file, folder: str = "uploaded", storage_id: str = None, format: str = "JPEG") -> str:
        if storage_id is None:
            storage_id = str(uuid.uuid4())
        ext = ".jpg" if format.upper() in {"JPEG", "JPG"} else f".{format.lower()}"
        file_path = temp_directories[folder] / f"{storage_id}{ext}"
        file_path.touch()
        return str(file_path)

    def read_side_effect(path):
        return open(path, "rb")

    def delete_side_effect(path):
        file_path = Path(path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    def exists_side_effect(path):
        return Path(path).is_file()

    def destination_path_side_effect(source, target_folder):
        return temp_directories[target_folder] / Path(source).name

    def move_side_effect(source, target_folder):
        source_path = Path(source)
        dest = temp_directories[target_folder] / source_path.name
        if source_path.exists():
            dest.write_bytes(source_path.read_bytes())
            source_path.unlink()
        return str(dest)

    mock.save.side_effect = save_side_effect
    mock.read.side_effect = read_side_effect
    mock.delete.side_effect = delete_side_effect
    mock.exists.side_effect = exists_side_effect
    mock.destination_path.side_effect = destination_path_side_effect
    mock.move.side_effect = move_side_effect
    return mock


@pytest.fixture
def mock_image_edit_service(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock ImageEditService."""
    mock = Mock(spec=ImageEditService)
    
    def edit_side_effect(image_name: str, *args, **kwargs):
        """Check if source image exists before processing."""
        source_path = temp_directories["uploaded"] / image_name
        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_name} not found in uploaded")
        output_name = f"{Path(image_name).stem}_resized.jpg"
        output_path = temp_directories["edited"] / output_name
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        return EditResultDTO(
            path=str(output_path),
            image=Mock(
                id="mock-id",
                filename=output_name,
                format="JPEG",
                mode="RGB",
                width=100,
                height=100,
                size_bytes=0,
                path=str(output_path),
                folder="edited",
                url=None,
            ),
        )
    
    mock.resize_image.side_effect = lambda img_name, w, h: edit_side_effect(img_name)
    mock.rotate_image.side_effect = lambda img_name, *args, **kwargs: edit_side_effect(img_name)
    mock.convert_to_grayscale.side_effect = lambda img_name: edit_side_effect(img_name)
    mock.blur_image.side_effect = lambda img_name, *args, **kwargs: edit_side_effect(img_name)
    mock.sharpen_image.side_effect = lambda img_name, *args, **kwargs: edit_side_effect(img_name)
    mock.adjust_brightness.side_effect = lambda img_name, *args, **kwargs: edit_side_effect(img_name)
    mock.adjust_contrast.side_effect = lambda img_name, *args, **kwargs: edit_side_effect(img_name)
    return mock


@pytest.fixture
def mock_detection_service(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock ObjectDetectionService with mocked DETR model."""
    mock = Mock(spec=ObjectDetectionService)
    
    mock_detections = [
        {
            "label": "person",
            "confidence": 0.95,
            "box": [100.0, 100.0, 200.0, 300.0]
        },
        {
            "label": "car",
            "confidence": 0.87,
            "box": [300.0, 150.0, 500.0, 400.0]
        }
    ]
    
    mock.get_bounding_boxes.return_value = str(temp_directories["detected"] / "test_bounding_boxes.jpg")
    mock.get_detected_objects.return_value = {
        "detections": mock_detections,
        "model_name": "facebook/detr-resnet-50",
        "model_version": None,
    }
    mock.detect_with_visualization.return_value = {
        "image_with_boxes": str(temp_directories["detected"] / "test_bounding_boxes.jpg"),
        "detections": mock_detections,
        "model_name": "facebook/detr-resnet-50",
        "model_version": None,
    }
    from app.vision.inference.engine import EngineMetadata

    mock.engine = Mock()
    detection_result = {
        "image_with_boxes": str(temp_directories["detected"] / "test_bounding_boxes.jpg"),
        "detections": mock_detections,
        "model_name": "facebook/detr-resnet-50",
        "model_version": None,
    }
    objects_result = {
        "detections": mock_detections,
        "model_name": "facebook/detr-resnet-50",
        "model_version": None,
    }

    def _resolve_image_path(filename: str, folder: str = "uploaded") -> Path:
        return temp_directories.get(folder, temp_directories["uploaded"]) / filename

    def detect_for_filename_side_effect(filename: str, folder: str = "uploaded"):
        if not _resolve_image_path(filename, folder).exists():
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {folder}")
        return detection_result

    def get_detected_objects_for_filename_side_effect(filename: str, folder: str = "uploaded"):
        if not _resolve_image_path(filename, folder).exists():
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {folder}")
        return objects_result

    mock.detect_for_filename.side_effect = detect_for_filename_side_effect
    mock.get_detected_objects_for_filename.side_effect = get_detected_objects_for_filename_side_effect
    mock.engine.metadata = EngineMetadata(
        model_name="facebook/detr-resnet-50",
        model_revision=None,
    )
    return mock


@pytest.fixture
def sample_image_rgb() -> Image.Image:
    """Create a sample RGB test image."""
    img = Image.new('RGB', (800, 600), color='red')
    return img


@pytest.fixture
def sample_image_rgba() -> Image.Image:
    """Create a sample RGBA test image."""
    img = Image.new('RGBA', (400, 300), color=(255, 0, 0, 128))
    return img


@pytest.fixture
def sample_image_file(temp_directories: Dict[str, Path], sample_image_rgb: Image.Image) -> Path:
    """Create a sample image file on disk."""
    image_path = temp_directories["uploaded"] / "test_image.jpg"
    sample_image_rgb.save(image_path, format="JPEG")
    return image_path


@pytest.fixture
def upload_file_factory():
    """Factory to create UploadFile objects for testing."""
    def _create_upload_file(
        content: bytes = b"fake image content",
        filename: str = "test.jpg",
        content_type: str = "image/jpeg"
    ) -> UploadFile:
        file_obj = BytesIO(content)
        return UploadFile(
            filename=filename,
            file=file_obj,
            headers={"content-type": content_type}
        )
    return _create_upload_file


@pytest.fixture
def valid_upload_file(upload_file_factory) -> UploadFile:
    """Create a valid UploadFile for testing."""
    img = Image.new('RGB', (100, 100), color='blue')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return UploadFile(
        filename="test.jpg",
        file=img_bytes,
        headers={"content-type": "image/jpeg"}
    )


@pytest.fixture
def mock_inference_engine(mock_detr_model):
    """Create a mock InferenceEngine backed by mocked DETR components."""
    from app.vision.inference.engine import EngineMetadata, InferenceEngine

    engine = Mock(spec=InferenceEngine)
    engine.processor = mock_detr_model["processor"]
    engine.model = mock_detr_model["model"]
    engine.metadata = EngineMetadata(
        model_name="facebook/detr-resnet-50",
        model_revision=None,
    )
    engine.is_ready = True
    engine.warmup = Mock()
    engine.predict = Mock()
    engine.inference_count = 0
    return engine


@pytest.fixture
def test_client(mock_inference_engine) -> TestClient:
    """Create a FastAPI test client with a mocked inference engine."""
    with patch(
        "app.core.lifespan.InferenceEngine.from_settings",
        return_value=mock_inference_engine,
    ):
        with TestClient(app) as client:
            yield client


@pytest.fixture
def test_client_with_overrides(
    temp_directories: Dict[str, Path],
    mock_local_storage: Mock,
    mock_image_edit_service: Mock,
    mock_image_service: Mock,
    mock_detection_service: Mock,
    mock_inference_engine: Mock,
) -> TestClient:
    """Create a FastAPI test client with dependency overrides."""
    def override_get_local_image_storage():
        return mock_local_storage

    def override_get_image_edit_service():
        return mock_image_edit_service

    def override_get_image_service():
        return mock_image_service

    def override_get_object_detection_service():
        return mock_detection_service

    app.dependency_overrides[get_local_image_storage] = override_get_local_image_storage
    app.dependency_overrides[get_image_edit_service] = override_get_image_edit_service
    app.dependency_overrides[get_image_service] = override_get_image_service
    app.dependency_overrides[get_object_detection_service] = override_get_object_detection_service

    with patch(
        "app.core.lifespan.InferenceEngine.from_settings",
        return_value=mock_inference_engine,
    ):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_detr_model():
    """Mock the DETR model to avoid loading actual model in tests."""
    with patch("app.vision.inference.engine.DetrImageProcessor") as mock_processor, \
         patch("app.vision.inference.engine.DetrForObjectDetection") as mock_model:
        
        # Mock processor
        mock_processor_instance = Mock()
        mock_processor_instance.from_pretrained.return_value = mock_processor_instance
        
        # Mock model outputs
        mock_outputs = Mock()
        mock_outputs.logits = Mock()
        mock_outputs.pred_boxes = Mock()
        
        mock_model_instance = Mock()
        mock_model_instance.from_pretrained.return_value = mock_model_instance
        mock_model_instance.config.id2label = {
            1: "person",
            3: "car",
            5: "bicycle"
        }
        
        def mock_post_process(outputs, target_sizes, threshold):
            return [{
                "scores": Mock(tolist=lambda: [0.95, 0.87]),
                "labels": Mock(tolist=lambda: [1, 3], item=lambda x: [1, 3][x]),
                "boxes": Mock(tolist=lambda: [[100, 100, 200, 300], [300, 150, 500, 400]])
            }]
        
        mock_processor_instance.post_process_object_detection = mock_post_process
        
        mock_processor.from_pretrained.return_value = mock_processor_instance
        mock_model.from_pretrained.return_value = mock_model_instance
        
        yield {
            "processor": mock_processor_instance,
            "model": mock_model_instance
        }


@pytest.fixture
def format_extensions() -> Dict[str, str]:
    """Get format extensions mapping."""
    return {
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "WEBP": ".webp"
    }


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for API endpoints")