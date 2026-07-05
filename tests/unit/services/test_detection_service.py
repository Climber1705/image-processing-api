"""
Unit tests for ObjectDetectionService.
"""

import pytest
from unittest.mock import Mock
from PIL import Image

from app.vision.detection_service import ObjectDetectionService
from app.vision.inference.schemas import Detection, DetectionResult


@pytest.mark.unit
class TestObjectDetectionService:
    """Test cases for ObjectDetectionService."""

    @pytest.fixture
    def mock_image_repository(self):
        mock = Mock()
        mock.resolve_image_id.return_value = "output-id"
        return mock

    @pytest.fixture
    def mock_image_service(self):
        return Mock()

    @pytest.fixture
    def detection_service(self, mock_local_storage, mock_inference_engine, mock_image_service, mock_image_repository):
        """Create ObjectDetectionService with mocked dependencies."""
        return ObjectDetectionService(
            inference_engine=mock_inference_engine,
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

    def test_image_to_bytesio(self, detection_service, sample_image_rgb):
        """Test converting PIL image to BytesIO."""
        image_bytes = detection_service._image_to_bytesio(sample_image_rgb)

        assert image_bytes is not None
        assert image_bytes.tell() == 0
        assert len(image_bytes.read()) > 0

    def test_get_detected_objects(self, detection_service, temp_directories, sample_result):
        """Test getting detected objects without visualization."""
        image_path = temp_directories["uploaded"] / "test_detect.jpg"
        img = Image.new("RGB", (800, 600), color="red")
        img.save(image_path, format="JPEG")

        detection_service.engine.predict.return_value = sample_result

        detections = detection_service.get_detected_objects(str(image_path))

        assert isinstance(detections, dict)
        assert len(detections["detections"]) == 2
        assert detections["detections"][0]["label"] == "person"
        detection_service.engine.predict.assert_called_once()

    def test_get_bounding_boxes(self, detection_service, temp_directories, sample_result, mock_local_storage):
        """Test getting bounding boxes with visualization."""
        image_path = temp_directories["uploaded"] / "test_boxes.jpg"
        img = Image.new("RGB", (800, 600), color="blue")
        img.save(image_path, format="JPEG")

        detection_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        output_path = detection_service.get_bounding_boxes(str(image_path), "test_boxes.jpg")

        assert output_path is not None
        assert "bounding_boxes" in output_path or "detected" in output_path
        detection_service.engine.predict.assert_called_once()
        detection_service.image_repository.create_record.assert_called_once()

    def test_detect_with_visualization_single_inference(
        self, detection_service, temp_directories, sample_result, mock_local_storage
    ):
        """Bounding-box flow must call predict exactly once."""
        image_path = temp_directories["uploaded"] / "test_single.jpg"
        img = Image.new("RGB", (800, 600), color="green")
        img.save(image_path, format="JPEG")

        detection_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = detection_service.detect_with_visualization(str(image_path), "test_single.jpg")

        assert result["image_with_boxes"] is not None
        assert len(result["detections"]) == 2
        assert result["model_name"] == "facebook/detr-resnet-50"
        detection_service.engine.predict.assert_called_once()
