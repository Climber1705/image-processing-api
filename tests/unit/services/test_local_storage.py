"""
Unit tests for LocalImageStorage service.
"""

import re
import uuid
import pytest
from pathlib import Path
from fastapi import HTTPException, status
from io import BytesIO
from PIL import Image

from app.storage.local_storage import LocalImageStorage


UUID_FILENAME_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$"
)


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

    def test_get_storage_filename_with_id(self, storage_service):
        """Test storage filename uses the provided UUID."""
        storage_id, filename = storage_service._get_storage_filename("abc-123-def", "JPEG")

        assert storage_id == "abc-123-def"
        assert filename == "abc-123-def.jpg"

    def test_get_storage_filename_generates_uuid(self, storage_service):
        """Test storage filename generates a UUID when none is provided."""
        storage_id, filename = storage_service._get_storage_filename(None, "JPEG")

        assert filename.endswith(".jpg")
        assert filename == f"{storage_id}.jpg"
        uuid.UUID(storage_id)

    def test_get_storage_filename_different_formats(self, storage_service):
        """Test storage filename generation for different formats."""
        formats = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif"
        }

        for format_name, expected_ext in formats.items():
            storage_id, filename = storage_service._get_storage_filename("test-id", format_name)
            assert filename == f"test-id{expected_ext}"

    def test_save_valid_image(self, storage_service, temp_directories, valid_upload_file):
        """Test saving a valid image with UUID storage name."""
        valid_upload_file.file.seek(0)
        file_path = storage_service.save(
            file=valid_upload_file.file,
            folder="uploaded",
            storage_id="11111111-1111-1111-1111-111111111111",
            format="JPEG"
        )

        assert Path(file_path).exists()
        assert Path(file_path).name == "11111111-1111-1111-1111-111111111111.jpg"

    def test_save_with_generated_uuid(self, storage_service, temp_directories, valid_upload_file):
        """Test saving image with auto-generated UUID filename."""
        valid_upload_file.file.seek(0)
        file_path = storage_service.save(
            file=valid_upload_file.file,
            folder="uploaded",
            storage_id=None,
            format="JPEG"
        )

        assert Path(file_path).exists()
        assert UUID_FILENAME_PATTERN.match(Path(file_path).name)

    def test_save_invalid_image(self, storage_service, temp_directories):
        """Test saving an invalid image file."""
        invalid_file = BytesIO(b"not an image")

        with pytest.raises(HTTPException) as exc_info:
            storage_service.save(invalid_file, folder="uploaded")

        assert exc_info.value.status_code == 400
        assert "not a valid image" in exc_info.value.detail

    def test_save_different_folders(self, storage_service, temp_directories, valid_upload_file):
        """Test saving images to different folders."""
        folders = ["uploaded", "edited", "detected"]

        for index, folder in enumerate(folders):
            valid_upload_file.file.seek(0)
            storage_id = f"22222222-2222-2222-2222-22222222222{index}"
            file_path = storage_service.save(
                file=valid_upload_file.file,
                folder=folder,
                storage_id=storage_id,
                format="JPEG"
            )

            assert Path(file_path).exists()
            assert folder in file_path

    def test_get_success(self, storage_service, temp_directories):
        """Test reading an existing file."""
        img = Image.new("RGB", (10, 10), color="red")
        test_file = temp_directories["uploaded"] / "test.jpg"
        img.save(test_file, format="JPEG")

        with storage_service.get("test.jpg") as file_handle:
            content = file_handle.read()

        assert content
        assert len(content) > 0

    def test_get_file_not_found(self, storage_service, mock_file_path_resolver):
        """Test reading a non-existent file."""
        mock_file_path_resolver.find_file.side_effect = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found"
        )

        with pytest.raises(HTTPException):
            storage_service.get("nonexistent.jpg")

    def test_delete_success(self, storage_service, temp_directories):
        """Test successful file deletion."""
        test_file = temp_directories["uploaded"] / "test_delete.jpg"
        test_file.touch()

        result = storage_service.delete("test_delete.jpg")

        assert result is True
        assert not test_file.exists()

    def test_delete_file_not_found(self, storage_service):
        """Test deleting non-existent file."""
        with pytest.raises(HTTPException):
            storage_service.delete("nonexistent.jpg")

    def test_delete_different_folders(self, storage_service, temp_directories):
        """Test deleting files from different folders."""
        folders = ["uploaded", "edited", "detected"]

        for folder in folders:
            test_file = temp_directories[folder] / "test.jpg"
            test_file.touch()

            result = storage_service.delete("test.jpg")

            assert result is True
            assert not test_file.exists()
