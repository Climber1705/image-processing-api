"""
Integration tests for image management API routes.
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi import status

@pytest.mark.integration
class TestImageRoutes:
    """Integration tests for /images endpoints."""

    def test_upload_image_success(self, test_client_with_overrides, temp_directories):
        """Test successful image upload."""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"file": ("test_upload.jpg", img_bytes, "image/jpeg")}
        data = {"filename": "test_upload", "format": "JPEG"}
        
        response = test_client_with_overrides.post("/images", files=files, data=data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "path" in response.json()
        assert response.json()["status"] == "success"

    def test_upload_image_invalid_format(self, test_client_with_overrides):
        """Test uploading invalid image format."""
        files = {"file": ("test.txt", BytesIO(b"not an image"), "text/plain")}
        
        response = test_client_with_overrides.post("/images", files=files)
        
        assert response.status_code in [400, 422]

    def test_get_images_list(self, test_client_with_overrides, temp_directories):
        """Test listing images."""
        for i in range(3):
            img_path = temp_directories["uploaded"] / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(img_path, format="JPEG")
        
        response = test_client_with_overrides.get("/images?folder=uploaded&limit=10&offset=0")
        
        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)

    def test_get_images_with_pagination(self, test_client_with_overrides, temp_directories):
        """Test listing images with pagination."""
        for i in range(5):  
            img_path = temp_directories["uploaded"] / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='green')
            img.save(img_path, format="JPEG")
        
        response = test_client_with_overrides.get("/images?folder=uploaded&limit=2&offset=0")
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) <= 2

    def test_get_image_detail(self, test_client_with_overrides, temp_directories):
        """Test getting image details."""
        img_path = temp_directories["uploaded"] / "test_detail.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(img_path, format="JPEG")
        
        response = test_client_with_overrides.get("/images/test_detail.jpg?folder=uploaded")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "filename" in data
        assert "width" in data
        assert "height" in data

    def test_get_image_detail_not_found(self, test_client_with_overrides):
        """Test getting details for non-existent image."""
        response = test_client_with_overrides.get("/images/nonexistent.jpg?folder=uploaded")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_image_dimensions(self, test_client_with_overrides, temp_directories):
        """Test getting image dimensions."""
        # Create test image
        img_path = temp_directories["uploaded"] / "test_dim.jpg"
        img = Image.new('RGB', (1920, 1080), color='blue')
        img.save(img_path, format="JPEG")
        
        response = test_client_with_overrides.get("/images/test_dim.jpg/dimensions?folder=uploaded")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["width"] == 1920
        assert data["height"] == 1080

    def test_delete_image_success(self, test_client_with_overrides, temp_directories):
        """Test successful image deletion."""
        img_path = temp_directories["uploaded"] / "test_delete.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(img_path, format="JPEG")
        
        response = test_client_with_overrides.delete("/images/test_delete.jpg?folder=uploaded")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_delete_image_not_found(self, test_client_with_overrides):
        """Test deleting non-existent image."""
        response = test_client_with_overrides.delete("/images/nonexistent.jpg?folder=uploaded")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_move_image_success(self, test_client_with_overrides, temp_directories):
        """Test successful image move."""
        img_path = temp_directories["uploaded"] / "test_move.jpg"
        img = Image.new('RGB', (100, 100), color='green')
        img.save(img_path, format="JPEG")
        
        data = {"source_folder": "uploaded", "target_folder": "edited"}
        response = test_client_with_overrides.patch("/images/test_move.jpg", json=data)
        
        assert response.status_code == status.HTTP_200_OK
        assert "filename" in response.json()

    def test_clear_all_images(self, test_client_with_overrides, temp_directories):
        """Test clearing all images."""
        for i in range(3):
            img_path = temp_directories["uploaded"] / f"test_clear_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(img_path, format="JPEG")
        
        response = test_client_with_overrides.delete("/images?folder=uploaded")
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"