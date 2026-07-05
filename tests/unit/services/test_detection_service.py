"""
Unit tests for InferenceService.
"""

import pytest
from unittest.mock import Mock
from PIL import Image

from app.vision.domain.dtos import DetectResponseDTO, DetectionsResultDTO
from app.vision.domain.errors import CorruptImageError, InferenceError, ModelNotReadyError
from app.vision.inference.schemas import Detection, DetectionResult
from app.vision.service import InferenceService


@pytest.mark.unit
class TestInferenceService:
    """Test cases for InferenceService."""

    @pytest.fixture
    def mock_image_repository(self):
        mock = Mock()
        mock.get_or_create_image_id.return_value = "output-id"
        return mock

    @pytest.fixture
    def mock_image_service(self):
        return Mock()

    @pytest.fixture
    def inference_service(self, mock_local_storage, mock_inference_engine, mock_image_service, mock_image_repository):
        """Create InferenceService with mocked dependencies."""
        mock_inference_engine.is_ready = True
        return InferenceService(
            engine=mock_inference_engine,
            storage=mock_local_storage,
            image_service=mock_image_service,
            image_repository=mock_image_repository,
        )

    @pytest.fixture
    def sample_result(self):
        return DetectionResult(
            detections=[
                Detection(label="person", confidence=0.95, box=[100.0, 100.0, 200.0, 300.0]),
                Detection(label="car", confidence=0.87, box=[300.0, 150.0, 500.0, 400.0]),
            ],
            model_name="facebook/detr-resnet-50",
            model_version=None,
        )

    def test_image_to_bytesio(self, inference_service, sample_image_rgb):
        """Test converting PIL image to BytesIO."""
        image_bytes = inference_service._image_to_bytesio(sample_image_rgb)

        assert image_bytes is not None
        assert image_bytes.tell() == 0
        assert len(image_bytes.read()) > 0

    def test_load_and_validate_image(self, inference_service, temp_directories):
        """Test valid image loading converts to RGB."""
        image_path = temp_directories["uploaded"] / "test_valid.png"
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(image_path, format="PNG")

        loaded = inference_service._load_and_validate_image(str(image_path))

        assert loaded.mode == "RGB"
        assert loaded.size == (100, 100)

    def test_load_and_validate_image_rejects_empty_file(self, inference_service, temp_directories):
        """Test empty files raise CorruptImageError."""
        image_path = temp_directories["uploaded"] / "empty.jpg"
        image_path.touch()

        with pytest.raises(CorruptImageError, match="empty"):
            inference_service._load_and_validate_image(str(image_path))

    def test_load_and_validate_image_rejects_corrupt_file(self, inference_service, temp_directories):
        """Test corrupt files raise CorruptImageError."""
        image_path = temp_directories["uploaded"] / "corrupt.jpg"
        image_path.write_text("not an image")

        with pytest.raises(CorruptImageError, match="corrupt"):
            inference_service._load_and_validate_image(str(image_path))

    def test_run_inference_requires_ready_engine(self, inference_service, temp_directories):
        """Test inference fails when engine is not ready."""
        image_path = temp_directories["uploaded"] / "test_ready.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(image_path, format="JPEG")
        inference_service.engine.is_ready = False

        with pytest.raises(ModelNotReadyError):
            inference_service._run_inference(str(image_path))

    def test_get_detected_objects(self, inference_service, temp_directories, sample_result):
        """Test getting detected objects without visualization."""
        image_path = temp_directories["uploaded"] / "test_detect.jpg"
        img = Image.new("RGB", (800, 600), color="red")
        img.save(image_path, format="JPEG")

        inference_service.engine.predict.return_value = sample_result

        result = inference_service.get_detected_objects(str(image_path))

        assert isinstance(result, DetectionsResultDTO)
        assert len(result.detections) == 2
        assert result.detections[0].label == "person"
        assert result.metadata.model_name == "facebook/detr-resnet-50"
        inference_service.engine.predict.assert_called_once()

    def test_detect_with_visualization(self, inference_service, temp_directories, sample_result, mock_local_storage):
        """Test detection with visualization persists annotated image."""
        image_path = temp_directories["uploaded"] / "test_boxes.jpg"
        img = Image.new("RGB", (800, 600), color="blue")
        img.save(image_path, format="JPEG")

        inference_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = inference_service.detect_with_visualization(str(image_path), "test_boxes.jpg")

        assert isinstance(result, DetectResponseDTO)
        assert result.image_path is not None
        assert len(result.detections) == 2
        assert result.metadata.model_name == "facebook/detr-resnet-50"
        inference_service.engine.predict.assert_called_once()
        inference_service.image_repository.upsert_record.assert_called_once()

    def test_detect_with_visualization_single_inference(
        self, inference_service, temp_directories, sample_result, mock_local_storage
    ):
        """Bounding-box flow must call predict exactly once."""
        image_path = temp_directories["uploaded"] / "test_single.jpg"
        img = Image.new("RGB", (800, 600), color="green")
        img.save(image_path, format="JPEG")

        inference_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = inference_service.detect_with_visualization(str(image_path), "test_single.jpg")

        assert result.image_path is not None
        assert len(result.detections) == 2
        inference_service.engine.predict.assert_called_once()

    def test_run_inference_wraps_engine_errors(self, inference_service, temp_directories):
        """Test engine failures are raised as InferenceError."""
        image_path = temp_directories["uploaded"] / "test_fail.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(image_path, format="JPEG")
        inference_service.engine.predict.side_effect = RuntimeError("Unable to infer channel dimension format")

        with pytest.raises(InferenceError, match="Inference failed"):
            inference_service._run_inference(str(image_path))
