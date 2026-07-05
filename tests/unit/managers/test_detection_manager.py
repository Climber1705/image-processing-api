"""
Unit tests for DetectionManager.
"""

import pytest
from fastapi import HTTPException

from app.managers.detection_manager import DetectionManager


@pytest.mark.unit
class TestDetectionManager:
    """Test cases for DetectionManager."""

    @pytest.fixture
    def detection_manager(self, mock_detection_service):
        """Create DetectionManager with mocked dependencies."""
        return DetectionManager(detection_service=mock_detection_service)

    def test_process_image_for_detection_success(self, detection_manager):
        """Test successful image processing for detection."""
        image_path = "/path/to/test.jpg"
        detection_manager.detection_service.detect_with_visualization.return_value = {
            "image_with_boxes": "/path/to/boxes.jpg",
            "detections": [{"label": "person", "confidence": 0.95, "box": [100, 100, 200, 300]}],
            "model_name": "facebook/detr-resnet-50",
            "model_version": None,
        }

        result = detection_manager.process_image_for_detection(image_path)

        assert "image_with_boxes" in result
        assert "detections" in result
        assert len(result["detections"]) > 0
        detection_manager.detection_service.detect_with_visualization.assert_called_once_with(image_path)
        detection_manager.detection_service.get_bounding_boxes.assert_not_called()
        detection_manager.detection_service.get_detected_objects.assert_not_called()

    def test_process_image_for_detection_error(self, detection_manager):
        """Test error handling in process_image_for_detection."""
        image_path = "/path/to/test.jpg"
        detection_manager.detection_service.detect_with_visualization.side_effect = Exception("Detection failed")

        with pytest.raises(HTTPException) as exc_info:
            detection_manager.process_image_for_detection(image_path)

        assert exc_info.value.status_code == 500

    def test_get_detected_objects_summary_success(self, detection_manager):
        """Test getting detected objects summary."""
        image_path = "/path/to/test.jpg"
        mock_detections = [
            {"label": "person", "confidence": 0.95, "box": [100, 100, 200, 300]},
            {"label": "car", "confidence": 0.87, "box": [300, 150, 500, 400]},
        ]
        detection_manager.detection_service.get_detected_objects.return_value = mock_detections

        result = detection_manager.get_detected_objects_summary(image_path)

        assert len(result["detections"]) == 2
        assert result["detections"][0]["label"] == "person"
        assert result["model_name"] == "facebook/detr-resnet-50"

    def test_get_detected_objects_summary_error(self, detection_manager):
        """Test error handling in get_detected_objects_summary."""
        image_path = "/path/to/test.jpg"
        detection_manager.detection_service.get_detected_objects.side_effect = Exception("Detection failed")

        with pytest.raises(RuntimeError):
            detection_manager.get_detected_objects_summary(image_path)
