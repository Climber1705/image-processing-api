"""
Unit tests for ImageManager.
"""

import pytest
from PIL import Image

from app.managers.image_manager import ImageManager


@pytest.mark.unit
class TestImageManager:
    """Test cases for ImageManager."""

    @pytest.fixture
    def image_manager(self, mock_local_storage, mock_image_crud_service, mock_metadata_extractor):
        """Create ImageManager with mocked dependencies."""
        return ImageManager(
            local_storage=mock_local_storage,
            image_CRUD=mock_image_crud_service,
            metadata_extractor=mock_metadata_extractor
        )

    def test_save_uploaded_image(self, image_manager, valid_upload_file):
        """Test saving uploaded image."""
        result = image_manager.save_uploaded_image(valid_upload_file, "test.jpg", "JPEG")
        
        assert result is not None
        image_manager.local_storage.save.assert_called_once()

    def test_get_image_path(self, image_manager):
        """Test getting image path."""
        path = image_manager.get_image_path("test.jpg", "uploaded")
        
        assert path is not None
        image_manager.image_CRUD.get_image_path.assert_called_once_with("test.jpg", "uploaded")

    def test_get_image_dimensions(self, image_manager, temp_directories):
        """Test getting image dimensions."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        image_path.touch()
        
        width, height = image_manager.get_image_dimensions(image_path)
        
        assert width == 800
        assert height == 600
        image_manager.metadata_extractor.get_dimensions.assert_called_once()

    def test_get_image_metadata(self, image_manager, temp_directories):
        """Test getting image metadata."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        image_path.touch()
        
        metadata = image_manager.get_image_metadata(image_path)
        
        assert metadata is not None
        assert "filename" in metadata
        image_manager.metadata_extractor.get_metadata.assert_called_once()

    def test_get_image_by_id(self, image_manager, temp_directories):
        """Test getting image by ID."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(image_path, format='JPEG')
        
        result = image_manager.get_image_by_id("test.jpg", "uploaded")
        
        assert result is not None
        image_manager.image_CRUD.get_image_by_id.assert_called_once_with("test.jpg", "uploaded")

    def test_list_images(self, image_manager):
        """Test listing images."""
        result = image_manager.list_images("uploaded", limit=10, offset=0)
        
        assert isinstance(result, list)
        image_manager.image_CRUD.list_images.assert_called_once_with("uploaded", 10, 0, None)

    def test_delete_image(self, image_manager, temp_directories):
        """Test deleting image."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(image_path, format='JPEG')
        
        result = image_manager.delete_image("test.jpg", "uploaded")
        
        assert result is not None
        image_manager.image_CRUD.delete_image.assert_called_once_with("test.jpg", "uploaded")

    def test_delete_all_images(self, image_manager):
        """Test deleting all images."""
        result = image_manager.delete_all_images("uploaded")
        
        assert result is not None
        image_manager.image_CRUD.delete_all_images.assert_called_once_with("uploaded")

    def test_move_image(self, image_manager, temp_directories):
        """Test moving image."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(image_path, format='JPEG')
        
        result = image_manager.move_image("test.jpg", "uploaded", "edited")
        
        assert result is not None
        image_manager.image_CRUD.move_image.assert_called_once_with("test.jpg", "uploaded", "edited")