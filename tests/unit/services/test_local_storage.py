"""
Unit tests for LocalImageStorage service.
"""

import pytest
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from io import BytesIO

from app.media.storage.local_storage import LocalImageStorage


@pytest.mark.unit
class TestLocalImageStorage:
    """Test cases for LocalImageStorage."""

    @pytest.fixture
    def storage_service(self, temp_directories, mock_directory_manager, mock_image_validator, mock_file_path_resolver):
        """Create LocalImageStorage with mocked dependencies."""
        return LocalImageStorage(
            directory_manager=mock_directory_manager,
            image_validator=mock_image_validator,
            file_resolver=mock_file_path_resolver
        )

    def test_get_file_name_with_custom_filename(self, storage_service):
        """Test filename generation with custom filename."""
        filename = storage_service._get_file_name("my_image", "JPEG")
        
        assert filename == "my_image.jpg"
        assert filename.endswith(".jpg")

    def test_get_file_name_with_uuid(self, storage_service):
        """Test filename generation with UUID when no filename provided."""
        filename = storage_service._get_file_name(None, "JPEG")
        
        assert filename.endswith(".jpg")
        assert len(filename) > 4  # UUID + extension

    def test_get_file_name_different_formats(self, storage_service):
        """Test filename generation for different formats."""
        formats = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif"
        }
        
        for format_name, expected_ext in formats.items():
            filename = storage_service._get_file_name("test", format_name)
            assert filename.endswith(expected_ext)

    def test_save_valid_image(self, storage_service, temp_directories, valid_upload_file):
        """Test saving a valid image."""
        file_path = storage_service.save(
            file=valid_upload_file,
            folder="uploaded",
            filename="test_save.jpg",
            format="JPEG"
        )
        
        assert Path(file_path).exists()
        assert file_path.endswith(".jpg")

    def test_save_with_uuid_filename(self, storage_service, temp_directories, valid_upload_file):
        """Test saving image with auto-generated UUID filename."""
        file_path = storage_service.save(
            file=valid_upload_file,
            folder="uploaded",
            filename=None,
            format="JPEG"
        )
        
        assert Path(file_path).exists()
        assert file_path.endswith(".jpg")

    def test_save_invalid_image(self, storage_service, temp_directories):
        """Test saving an invalid image file."""
        invalid_file = UploadFile(
            filename="invalid.txt",
            file=BytesIO(b"not an image"),
            headers={"content-type": "text/plain"}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            storage_service.save(invalid_file, folder="uploaded")
        
        assert exc_info.value.status_code == 400
        assert "not a valid image" in exc_info.value.detail

    def test_save_different_folders(self, storage_service, temp_directories, valid_upload_file):
        """Test saving images to different folders."""
        folders = ["uploaded", "edited", "detected"]
        
        for folder in folders:
            file_path = storage_service.save(
                file=valid_upload_file,
                folder=folder,
                filename=f"test_{folder}.jpg",
                format="JPEG"
            )
            
            assert Path(file_path).exists()
            assert folder in file_path

    def test_get_url_success(self, storage_service, temp_directories):
        """Test getting URL for existing file."""
        test_file = temp_directories["uploaded"] / "test.jpg"
        test_file.touch()
        
        url = storage_service.get_url("test.jpg")
        
        assert url is not None
        assert isinstance(url, (str, Path))

    def test_get_url_file_not_found(self, storage_service, mock_file_path_resolver):
        """Test getting URL for non-existent file."""   
        mock_file_path_resolver.find_file.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found"
        )
        
        with pytest.raises(HTTPException):
            storage_service.get_url("nonexistent.jpg")

    def test_delete_success(self, storage_service, temp_directories):
        """Test successful file deletion."""
        test_file = temp_directories["uploaded"] / "test_delete.jpg"
        test_file.touch()
        
        result = storage_service.delete("uploaded", "test_delete.jpg")
        
        assert result is True
        assert not test_file.exists()

    def test_delete_file_not_found(self, storage_service):
        """Test deleting non-existent file."""
        result = storage_service.delete("uploaded", "nonexistent.jpg")
        
        assert result is False

    def test_delete_different_folders(self, storage_service, temp_directories):
        """Test deleting files from different folders."""
        folders = ["uploaded", "edited", "detected"]
        
        for folder in folders:
            test_file = temp_directories[folder] / "test.jpg"
            test_file.touch()
            
            result = storage_service.delete(folder, "test.jpg")
            
            assert result is True
            assert not test_file.exists()