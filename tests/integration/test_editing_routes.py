"""
Integration tests for image editing API routes.
"""

import pytest
from fastapi import status
from PIL import Image


@pytest.mark.integration
class TestEditingRoutes:
    """Integration tests for /images/{image_name}/edits endpoints."""

    def test_resize_image(self, test_client_with_overrides, temp_directories):
        """Test resizing an image."""
        img_path = temp_directories["uploaded"] / "test_resize.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test_resize.jpg/edits/resize?width=400&height=300"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_resize_image_invalid_dimensions(self, test_client_with_overrides, temp_directories):
        """Test resizing with invalid dimensions."""
        img_path = temp_directories["uploaded"] / "test.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test.jpg/edits/resize?width=-100&height=300"
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_convert_to_grayscale(self, test_client_with_overrides, temp_directories):
        """Test converting image to grayscale."""
        img_path = temp_directories["uploaded"] / "test_gray.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test_gray.jpg/edits/grayscale"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_rotate_image(self, test_client_with_overrides, temp_directories):
        """Test rotating an image."""
        img_path = temp_directories["uploaded"] / "test_rotate.jpg"
        img = Image.new('RGB', (100, 200), color='green')
        img.save(img_path, format="JPEG")

        data = {"degrees": 90, "expand": True}
        response = test_client_with_overrides.post(
            "/images/test_rotate.jpg/edits/rotate",
            json=data
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_blur_image(self, test_client_with_overrides, temp_directories):
        """Test applying blur filter."""
        img_path = temp_directories["uploaded"] / "test_blur.jpg"
        img = Image.new('RGB', (100, 100), color='yellow')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test_blur.jpg/edits/blur?radius=5.0"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_sharpen_image(self, test_client_with_overrides, temp_directories):
        """Test applying sharpen filter."""
        img_path = temp_directories["uploaded"] / "test_sharpen.jpg"
        img = Image.new('RGB', (100, 100), color='purple')
        img.save(img_path, format="JPEG")

        data = {"factor": 2.0, "radius": 2.0, "threshold": 3}
        response = test_client_with_overrides.post(
            "/images/test_sharpen.jpg/edits/sharpen",
            json=data
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_adjust_brightness(self, test_client_with_overrides, temp_directories):
        """Test adjusting image brightness."""
        img_path = temp_directories["uploaded"] / "test_brightness.jpg"
        img = Image.new('RGB', (100, 100), color='orange')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test_brightness.jpg/edits/brightness?factor=1.5"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_adjust_contrast(self, test_client_with_overrides, temp_directories):
        """Test adjusting image contrast."""
        img_path = temp_directories["uploaded"] / "test_contrast.jpg"
        img = Image.new('RGB', (100, 100), color='cyan')
        img.save(img_path, format="JPEG")

        response = test_client_with_overrides.post(
            "/images/test_contrast.jpg/edits/contrast?factor=1.2"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "path" in response.json()

    def test_edit_image_not_found(self, test_client_with_overrides):
        """Test editing non-existent image."""
        response = test_client_with_overrides.post(
            "/images/nonexistent.jpg/edits/resize?width=400&height=300"
        )

        assert response.status_code in [404, 500]
