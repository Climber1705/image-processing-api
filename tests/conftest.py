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
from app.core.dependencies import get_directories
from app.utils.file_operations.directory_utils import DirectoryManager, get_directory_manager
from app.utils.file_operations.file_utils import FilePathResolver, get_file_path_resolver
from app.utils.validator.simple_validator import SimpleImageValidator, get_simple_image_validator
from app.services.image.storage.local_storage import LocalImageStorage, get_local_image_storage
from app.services.image.crud_operations import ImageCRUDService, get_image_crud_service
from app.services.image.metadata_handler import ImageMetadataExtractor, get_image_metadata_extractor
from app.services.image.image_editor import ImageEditService, get_image_edit_service
from app.services.detection.detection_service import ObjectDetectionService, get_object_detection_service
from app.managers.image_manager import ImageManager, get_image_manager
from app.managers.edit_manager import EditManager, get_edit_manager
from app.managers.detection_manager import DetectionManager, get_detection_manager


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
def mock_file_path_resolver(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock FilePathResolver."""
    mock = Mock(spec=FilePathResolver)
    
    def find_file_side_effect(filename: str) -> Path:
        for dir_path in temp_directories.values():
            file_path = dir_path / filename
            if file_path.exists():
                return file_path
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No file named '{filename}' exists"
        )
    
    mock.find_file.side_effect = find_file_side_effect
    mock.find_and_validate_image.side_effect = lambda name: str(find_file_side_effect(name))
    return mock


@pytest.fixture
def mock_image_validator() -> Mock:
    """Create a mock SimpleImageValidator."""
    mock = Mock(spec=SimpleImageValidator)
    
    def validate_side_effect(file: UploadFile):
        """Validate file type - reject non-image files."""
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}. Allowed types: image/jpeg, image/png")
    
    def validate_type_side_effect(file: UploadFile):
        """Validate file type."""
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}. Allowed types: image/jpeg, image/png")
    
    mock.validate.side_effect = validate_side_effect
    mock.validate_type.side_effect = validate_type_side_effect
    mock.validate_size.return_value = None
    mock.validate_format.side_effect = lambda fmt: fmt.upper()
    mock.get_extension.side_effect = lambda fmt: {
        "JPEG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif"
    }.get(fmt.upper(), ".jpg")
    return mock


@pytest.fixture
def mock_metadata_extractor() -> Mock:
    """Create a mock ImageMetadataExtractor."""
    mock = Mock(spec=ImageMetadataExtractor)
    
    def get_dimensions_side_effect(image_path):
        """Get actual dimensions from image file if it exists."""
        try:
            with Image.open(image_path) as img:
                return (img.width, img.height)
        except (FileNotFoundError, OSError):
            return (800, 600)
    
    def get_metadata_side_effect(image_path):
        """Get actual metadata from image file if it exists."""
        try:
            with Image.open(image_path) as img:
                return {
                    "filename": Path(image_path).name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size_bytes": os.path.getsize(image_path) if os.path.exists(image_path) else 102400,
                    "path": str(image_path),
                    "url": None
                }
        except (FileNotFoundError, OSError):
            return {
                "filename": Path(image_path).name if isinstance(image_path, (str, Path)) else "test.jpg",
                "format": "JPEG",
                "mode": "RGB",
                "width": 800,
                "height": 600,
                "size_bytes": 102400,
                "path": str(image_path) if isinstance(image_path, (str, Path)) else "/path/to/test.jpg",
                "url": None
            }
    
    mock.get_dimensions.side_effect = get_dimensions_side_effect
    mock.get_metadata.side_effect = get_metadata_side_effect
    return mock


@pytest.fixture
def mock_image_crud_service(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock ImageCRUDService."""
    mock = Mock(spec=ImageCRUDService)
    
    def get_image_path_side_effect(image_name: str, folder: str = "uploaded") -> Path:
        return temp_directories.get(folder, temp_directories["uploaded"]) / image_name
    
    mock.get_image_path.side_effect = get_image_path_side_effect
    mock.list_images.return_value = []
    def get_image_by_id_side_effect(image_id: str, folder: str = "uploaded"):
        image_path = temp_directories.get(folder, temp_directories["uploaded"]) / image_id
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder}")
        try:
            with Image.open(image_path) as img:
                return {
                    "filename": Path(image_path).name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size_bytes": os.path.getsize(image_path) if os.path.exists(image_path) else 102400,
                    "path": str(image_path),
                    "url": None
                }
        except (FileNotFoundError, OSError):
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder}")
    
    mock.get_image_by_id.side_effect = get_image_by_id_side_effect
    def delete_image_side_effect(image_id: str, folder: str = "uploaded"):
        image_path = temp_directories.get(folder, temp_directories["uploaded"]) / image_id
        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder} folder")
        if image_path.exists():
            image_path.unlink()
        return {
            "status": "success",
            "message": f"Image {image_id} deleted from {folder}",
            "deleted_image": {}
        }
    mock.delete_image.side_effect = delete_image_side_effect
    mock.delete_all_images.return_value = {
        "status": "success",
        "message": "All images deleted",
        "count": 0
    }
    def move_image_side_effect(image_id: str, source_folder: str, target_folder: str):
        source_path = temp_directories.get(source_folder, temp_directories["uploaded"]) / image_id
        target_path = temp_directories.get(target_folder, temp_directories["edited"]) / image_id
        
        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {source_folder}")
        if target_path.exists():
            raise HTTPException(status_code=409, detail=f"Image {image_id} already exists in {target_folder}")
        
        shutil.move(str(source_path), str(target_path))

        try:
            with Image.open(target_path) as img:
                return {
                    "filename": Path(target_path).name,
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                    "size_bytes": os.path.getsize(target_path) if os.path.exists(target_path) else 102400,
                    "path": str(target_path),
                    "url": None
                }
        except (FileNotFoundError, OSError):
            return {
                "filename": Path(target_path).name,
                "format": "JPEG",
                "mode": "RGB",
                "width": 800,
                "height": 600,
                "size_bytes": 102400,
                "path": str(target_path),
                "url": None
            }
    
    mock.move_image.side_effect = move_image_side_effect
    return mock


@pytest.fixture
def mock_local_storage(temp_directories: Dict[str, Path]) -> Mock:
    """Create a mock LocalImageStorage."""
    mock = Mock(spec=LocalImageStorage)
    
    def save_side_effect(file: UploadFile, folder: str = "uploaded", filename: str = None, format: str = "JPEG") -> str:
        if filename is None:
            filename = f"{uuid.uuid4()}.jpg"
        file_path = temp_directories[folder] / filename
        file_path.touch()
        return str(file_path)
    
    mock.save.side_effect = save_side_effect
    mock.get_url.return_value = str(temp_directories["uploaded"] / "test.jpg")
    mock.delete.return_value = True
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
        return str(output_path)
    
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
    mock.get_detected_objects.return_value = mock_detections
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
    from app.services.inference.engine import EngineMetadata, InferenceEngine

    engine = Mock(spec=InferenceEngine)
    engine.processor = mock_detr_model["processor"]
    engine.model = mock_detr_model["model"]
    engine.metadata = EngineMetadata(
        model_name="facebook/detr-resnet-50",
        model_revision=None,
    )
    engine.is_ready = True
    engine.warmup = Mock()
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
    mock_directory_manager: Mock,
    mock_file_path_resolver: Mock,
    mock_image_validator: Mock,
    mock_metadata_extractor: Mock,
    mock_image_crud_service: Mock,
    mock_local_storage: Mock,
    mock_image_edit_service: Mock,
    mock_detection_service: Mock,
    mock_inference_engine: Mock,
) -> TestClient:
    """Create a FastAPI test client with dependency overrides."""
    def override_get_directories():
        return temp_directories
    
    def override_get_directory_manager():
        return mock_directory_manager
    
    def override_get_file_path_resolver():
        return mock_file_path_resolver
    
    def override_get_simple_image_validator():
        return mock_image_validator
    
    def override_get_image_metadata_extractor():
        return mock_metadata_extractor
    
    def override_get_image_crud_service():
        return mock_image_crud_service
    
    def override_get_local_image_storage():
        return mock_local_storage
    
    def override_get_image_edit_service():
        return mock_image_edit_service
    
    def override_get_object_detection_service():
        return mock_detection_service
    
    def override_get_image_manager():
        return ImageManager(
            directory_manager=mock_directory_manager,
            local_storage=mock_local_storage,
            image_CRUD=mock_image_crud_service,
            metadata_extractor=mock_metadata_extractor
        )
    
    def override_get_edit_manager():
        return EditManager(edit_service=mock_image_edit_service)
    
    def override_get_detection_manager():
        return DetectionManager(detection_service=mock_detection_service)
    
    app.dependency_overrides[get_directories] = override_get_directories
    app.dependency_overrides[get_directory_manager] = override_get_directory_manager
    app.dependency_overrides[get_file_path_resolver] = override_get_file_path_resolver
    app.dependency_overrides[get_simple_image_validator] = override_get_simple_image_validator
    app.dependency_overrides[get_image_metadata_extractor] = override_get_image_metadata_extractor
    app.dependency_overrides[get_image_crud_service] = override_get_image_crud_service
    app.dependency_overrides[get_local_image_storage] = override_get_local_image_storage
    app.dependency_overrides[get_image_edit_service] = override_get_image_edit_service
    app.dependency_overrides[get_object_detection_service] = override_get_object_detection_service
    app.dependency_overrides[get_image_manager] = override_get_image_manager
    app.dependency_overrides[get_edit_manager] = override_get_edit_manager
    app.dependency_overrides[get_detection_manager] = override_get_detection_manager

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
    with patch("app.services.inference.engine.DetrImageProcessor") as mock_processor, \
         patch("app.services.inference.engine.DetrForObjectDetection") as mock_model:
        
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