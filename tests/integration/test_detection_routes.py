"""
Integration tests for object detection API routes.
"""

import pytest
from PIL import Image
from fastapi import status


@pytest.mark.integration
class TestDetectionRoutes:
    """Integration tests for /images/{image_name}/detections endpoints."""

    def test_bounding_boxes_endpoint(self, test_client_with_overrides, temp_directories, mock_detection_service):
        """Test getting bounding boxes for detected objects."""
        img_path = temp_directories["uploaded"] / "test_detect.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test_detect.jpg/detections/bounding-boxes"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data or "path" in data or "image_with_boxes" in data

    def test_detected_objects_endpoint(self, test_client_with_overrides, temp_directories, mock_detection_service):
        """Test getting detected objects metadata."""
        img_path = temp_directories["uploaded"] / "test_objects.jpg"
        img = Image.new('RGB', (800, 600), color='blue')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.get(
            "/images/test_objects.jpg/detections"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_detection_image_not_found(self, test_client_with_overrides):
        """Test detection with non-existent image."""
        response = test_client_with_overrides.post(
            "/images/nonexistent.jpg/detections/bounding-boxes"
        )

        assert response.status_code in [400, 404, 500]
