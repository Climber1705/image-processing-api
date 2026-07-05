"""
Unit tests for LocalImageStorage service.
"""

import re
import uuid
import pytest
from pathlib import Path
from fastapi import HTTPException
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
    def storage_service(self, temp_directories, mock_image_validator):
        """Create LocalImageStorage with test directories."""
        return LocalImageStorage(
            directories=temp_directories,
            format_helper=mock_image_validator,
        )

    def test_save_valid_image(self, storage_service, temp_directories, valid_upload_file):
        """Test saving a valid image with UUID storage name."""
        valid_upload_file.file.seek(0)
        file_path = storage_service.save(
            file=valid_upload_file.file,
            folder="uploaded",
            storage_id="11111111-1111-1111-1111-111111111111",
            format="JPEG",
        )

        assert Path(file_path).exists()
        assert Path(file_path).name == "11111111-1111-1111-1111-111111111111.jpg"

    def test_save_different_formats(self, storage_service, temp_directories, valid_upload_file):
        """Test saving images with different formats."""
        formats = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif",
        }

        for format_name, expected_ext in formats.items():
            valid_upload_file.file.seek(0)
            storage_id = str(uuid.uuid4())
            file_path = storage_service.save(
                file=valid_upload_file.file,
                folder="uploaded",
                storage_id=storage_id,
                format=format_name,
            )
            assert Path(file_path).name == f"{storage_id}{expected_ext}"

    def test_save_invalid_image(self, storage_service):
        """Test saving an invalid image file."""
        invalid_file = BytesIO(b"not an image")

        with pytest.raises(HTTPException) as exc_info:
            storage_service.save(
                invalid_file,
                folder="uploaded",
                storage_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            )

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
                format="JPEG",
            )

            assert Path(file_path).exists()
            assert folder in file_path

    def test_read_success(self, storage_service, temp_directories):
        """Test reading an existing file by path."""
        img = Image.new("RGB", (10, 10), color="red")
        test_file = temp_directories["uploaded"] / "test.jpg"
        img.save(test_file, format="JPEG")

        with storage_service.read(test_file) as file_handle:
            content = file_handle.read()

        assert content
        assert len(content) > 0

    def test_read_file_not_found(self, storage_service, temp_directories):
        """Test reading a non-existent file."""
        with pytest.raises(FileNotFoundError):
            storage_service.read(temp_directories["uploaded"] / "missing.jpg")

    def test_delete_success(self, storage_service, temp_directories):
        """Test successful file deletion by path."""
        test_file = temp_directories["uploaded"] / "test_delete.jpg"
        test_file.touch()

        result = storage_service.delete(test_file)

        assert result is True
        assert not test_file.exists()

    def test_delete_file_not_found(self, storage_service, temp_directories):
        """Test deleting non-existent file returns False."""
        result = storage_service.delete(temp_directories["uploaded"] / "nonexistent.jpg")
        assert result is False

    def test_exists(self, storage_service, temp_directories):
        """Test path existence check."""
        test_file = temp_directories["uploaded"] / "exists.jpg"
        test_file.touch()

        assert storage_service.exists(test_file) is True
        assert storage_service.exists(temp_directories["uploaded"] / "missing.jpg") is False

    def test_destination_path(self, storage_service, temp_directories):
        """Test destination path computation for moves."""
        source = temp_directories["uploaded"] / "uuid-file.jpg"
        dest = storage_service.destination_path(source, "edited")

        assert dest == temp_directories["edited"] / "uuid-file.jpg"

    def test_move(self, storage_service, temp_directories):
        """Test moving a file between folders."""
        source = temp_directories["uploaded"] / "move-me.jpg"
        Image.new("RGB", (10, 10), color="blue").save(source, format="JPEG")

        new_path = storage_service.move(source, "edited")

        assert not source.exists()
        assert Path(new_path).exists()
        assert Path(new_path).parent == temp_directories["edited"]
