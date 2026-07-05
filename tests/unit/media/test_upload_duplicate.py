"""
Unit tests for duplicate upload detection.
"""

import pytest
from io import BytesIO
from unittest.mock import Mock

from PIL import Image

from app.media.domain.dtos import ImageDTO
from app.media.service import ImageService
from app.storage.local_storage import LocalImageStorage


@pytest.mark.unit
class TestDuplicateUpload:
    @pytest.fixture
    def image_service(self, temp_directories, mock_image_validator):
        return ImageService(
            repository=Mock(),
            storage=LocalImageStorage(
                directories=temp_directories,
                format_helper=mock_image_validator,
            ),
            validator=mock_image_validator,
        )

    def _upload_file(self, name: str = "photo.jpg"):
        image = Image.new("RGB", (50, 50), color="red")
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        upload = Mock()
        upload.filename = name
        upload.file = buffer
        return upload

    def test_upload_returns_existing_on_duplicate_content(self, image_service):
        existing_record = Mock()
        existing_record.id = "existing-id"
        existing_record.filename = "original.jpg"
        existing_record.path = "/tmp/original.jpg"
        existing_record.format = "JPEG"
        existing_record.mode = "RGB"
        existing_record.width = 50
        existing_record.height = 50
        existing_record.size_bytes = 1024
        existing_record.folder = "uploaded"
        image_service.repository.get_by_content_hash.return_value = existing_record

        result = image_service.upload_image(self._upload_file("copy.jpg"))

        assert result.path == "/tmp/original.jpg"
        assert result.image.filename == "original.jpg"
        image_service.repository.generate_image_id.assert_not_called()
        image_service.repository.create_upload_record.assert_not_called()

    def test_upload_creates_new_image(self, image_service):
        image_service.repository.get_by_content_hash.return_value = None
        image_service.repository.generate_image_id.return_value = "new-id"
        image_service.repository.create_upload_record.return_value = ImageDTO(
            id="new-id",
            filename="photo.jpg",
            format="JPEG",
            mode="RGB",
            width=50,
            height=50,
            size_bytes=1024,
            path="/tmp/photo.jpg",
            folder="uploaded",
        )

        result = image_service.upload_image(self._upload_file("photo.jpg"))

        image_service.repository.create_upload_record.assert_called_once()
        assert result.image.id == "new-id"
