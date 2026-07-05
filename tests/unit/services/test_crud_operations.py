"""
Unit tests for ImageCRUDService.
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException
from PIL import Image
from pathlib import Path

from app.media.crud_operations import ImageCRUDService
from app.schemas.image.image_responses import ImageListItem


@pytest.mark.unit
class TestImageCRUDService:
    """Test cases for ImageCRUDService."""

    @pytest.fixture
    def crud_service(self, temp_directories):
        """Create ImageCRUDService with mocked dependencies."""
        mock_dir_manager = Mock()
        mock_dir_manager.get_directory.side_effect = lambda folder: temp_directories.get(folder)
        mock_dir_manager.validate_folder.side_effect = lambda folder: folder in temp_directories
        
        mock_metadata_extractor = Mock()
        def get_metadata_side_effect(image_path):
            return {
                "filename": Path(image_path).name,
                "format": "JPEG",
                "mode": "RGB",
                "width": 800,
                "height": 600,
                "size_bytes": 102400,
                "path": str(image_path),
                "url": None
            }
        mock_metadata_extractor.get_metadata.side_effect = get_metadata_side_effect
        
        mock_file_resolver = Mock()
        
        return ImageCRUDService(
            directory_manager=mock_dir_manager,
            metadata_extractor=mock_metadata_extractor,
            file_resolver=mock_file_resolver,
            directories=temp_directories
        )

    def test_get_folder_map(self, crud_service):
        """Test folder mapping logic."""
        folder_map = crud_service._get_folder_map()
        
        assert "uploaded" in folder_map
        assert "edited" in folder_map
        assert "detected" in folder_map
        assert "all" in folder_map
        assert len(folder_map["all"]) == 3

    def test_list_images_uploaded_folder(self, crud_service, temp_directories):
        """Test listing images from uploaded folder."""
        for i in range(5):
            img_path = temp_directories["uploaded"] / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_path, format="JPEG")
        
        results = crud_service.list_images("uploaded", limit=10, offset=0)
        
        assert len(results) == 5
        assert all(isinstance(item, ImageListItem) for item in results)

    def test_list_images_with_pagination(self, crud_service, temp_directories):
        """Test listing images with pagination."""
        for i in range(10):
            img_path = temp_directories["uploaded"] / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(img_path, format="JPEG")
        
        results = crud_service.list_images("uploaded", limit=5, offset=0)
        assert len(results) == 5
        
        results = crud_service.list_images("uploaded", limit=5, offset=5)
        assert len(results) == 5

    def test_list_images_all_folders(self, crud_service, temp_directories):
        """Test listing images from all folders."""
        for folder in ["uploaded", "edited", "detected"]:
            img_path = temp_directories[folder] / "test.jpg"
            img = Image.new('RGB', (100, 100), color='green')
            img.save(img_path, format="JPEG")
        
        results = crud_service.list_images("all", limit=100, offset=0)
        
        assert len(results) >= 3

    def test_get_image_by_id_success(self, crud_service, temp_directories):
        """Test getting image by ID successfully."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(image_path, format="JPEG")
        
        result = crud_service.get_image_by_id("test.jpg", "uploaded")
        
        assert result["filename"] == "test.jpg"
        assert result["format"] == "JPEG"

    def test_get_image_by_id_not_found(self, crud_service):
        """Test getting image by ID when image doesn't exist."""
        with pytest.raises(HTTPException) as exc_info:
            crud_service.get_image_by_id("nonexistent.jpg", "uploaded")
        
        assert exc_info.value.status_code == 404

    def test_delete_image_success(self, crud_service, temp_directories):
        """Test successful image deletion."""
        image_path = temp_directories["uploaded"] / "test_delete.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(image_path, format="JPEG")
        
        result = crud_service.delete_image("test_delete.jpg", "uploaded")
        
        assert result["status"] == "success"
        assert not image_path.exists()

    def test_delete_image_not_found(self, crud_service):
        """Test deleting non-existent image."""
        with pytest.raises(HTTPException) as exc_info:
            crud_service.delete_image("nonexistent.jpg", "uploaded")
        
        assert exc_info.value.status_code == 404

    def test_delete_all_images_single_folder(self, crud_service, temp_directories):
        """Test deleting all images from a single folder."""
        for i in range(5):
            img_path = temp_directories["uploaded"] / f"test_{i}.jpg"
            img = Image.new('RGB', (100, 100), color='blue')
            img.save(img_path, format="JPEG")
        
        result = crud_service.delete_all_images("uploaded")
        
        assert result["status"] == "success"
        assert result["message"] == "Deleted 5 images from uploaded"
        assert len(list(temp_directories["uploaded"].glob("*.jpg"))) == 0

    def test_delete_all_images_all_folders(self, crud_service, temp_directories):
        """Test deleting all images from all folders."""
        for folder in ["uploaded", "edited", "detected"]:
            for i in range(2):
                img_path = temp_directories[folder] / f"test_{i}.jpg"
                img = Image.new('RGB', (100, 100), color='green')
                img.save(img_path, format="JPEG")
        
        result = crud_service.delete_all_images("all")
        
        assert result["status"] == "success"
        assert "Deleted" in result["message"]

    def test_delete_all_images_invalid_folder(self, crud_service):
        """Test deleting all images with invalid folder name."""
        with pytest.raises(HTTPException) as exc_info:
            crud_service.delete_all_images("invalid_folder")
        
        assert exc_info.value.status_code == 400

    def test_move_image_success(self, crud_service, temp_directories):
        """Test successful image move."""
        source_path = temp_directories["uploaded"] / "test_move.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(source_path, format="JPEG")
        
        result = crud_service.move_image("test_move.jpg", "uploaded", "edited")
        
        assert result["filename"] == "test_move.jpg"
        assert not source_path.exists()
        assert (temp_directories["edited"] / "test_move.jpg").exists()

    def test_move_image_same_folders(self, crud_service, temp_directories):
        """Test moving image to same folder (should fail)."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(image_path, format="JPEG")
        
        with pytest.raises(HTTPException) as exc_info:
            crud_service.move_image("test.jpg", "uploaded", "uploaded")
        
        assert exc_info.value.status_code == 400

    def test_move_image_not_found(self, crud_service):
        """Test moving non-existent image."""
        with pytest.raises(HTTPException) as exc_info:
            crud_service.move_image("nonexistent.jpg", "uploaded", "edited")
        
        assert exc_info.value.status_code == 404

    def test_move_image_target_exists(self, crud_service, temp_directories):
        """Test moving image when target already exists."""
        source_path = temp_directories["uploaded"] / "test.jpg"
        target_path = temp_directories["edited"] / "test.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(source_path, format="JPEG")
        img.save(target_path, format="JPEG")
        
        with pytest.raises(HTTPException) as exc_info:
            crud_service.move_image("test.jpg", "uploaded", "edited")
        
        assert exc_info.value.status_code == 409