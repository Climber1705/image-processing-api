"""
Unit tests for ObjectDetectionService.
"""

import pytest
from unittest.mock import Mock, patch
from PIL import Image

from app.vision.detection_service import ObjectDetectionService
from app.vision.inference.schemas import Detection, DetectionResult


@pytest.mark.unit
class TestObjectDetectionService:
    """Test cases for ObjectDetectionService."""

    @pytest.fixture
    def detection_service(self, mock_local_storage, mock_inference_engine):
        """Create ObjectDetectionService with mocked dependencies."""
        return ObjectDetectionService(
            inference_engine=mock_inference_engine,
            local_storage=mock_local_storage,
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

    def test_pillow_to_uploadfile(self, detection_service, sample_image_rgb):
        """Test converting PIL image to UploadFile."""
        upload_file = detection_service._pillow_to_uploadfile(sample_image_rgb, "test.png")

        assert upload_file.filename == "test.png"
        assert upload_file.file is not None

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

        def mock_save(file, folder, filename, format):
            output_path = temp_directories[folder] / filename
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        output_path = detection_service.get_bounding_boxes(str(image_path))

        assert output_path is not None
        assert "bounding_boxes" in output_path or "detected" in output_path
        detection_service.engine.predict.assert_called_once()

    def test_detect_with_visualization_single_inference(
        self, detection_service, temp_directories, sample_result, mock_local_storage
    ):
        """Bounding-box flow must call predict exactly once."""
        image_path = temp_directories["uploaded"] / "test_single.jpg"
        img = Image.new("RGB", (800, 600), color="green")
        img.save(image_path, format="JPEG")

        detection_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, filename, format):
            output_path = temp_directories[folder] / filename
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = detection_service.detect_with_visualization(str(image_path))

        assert result["image_with_boxes"] is not None
        assert len(result["detections"]) == 2
        assert result["model_name"] == "facebook/detr-resnet-50"
        detection_service.engine.predict.assert_called_once()
