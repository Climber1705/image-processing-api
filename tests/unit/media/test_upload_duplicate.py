"""
Unit tests for duplicate upload detection.
"""

import pytest
from io import BytesIO
from unittest.mock import Mock
from PIL import Image

from app.media.dtos import ImageDTO
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
        img = Image.new("RGB", (50, 50), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        upload = Mock()
        upload.filename = name
        upload.file = buffer
        return upload

    def test_upload_returns_existing_on_duplicate_content(self, image_service):
        existing = Mock()
        existing.id = "existing-id"
        existing.filename = "original.jpg"
        existing.path = "/tmp/original.jpg"
        existing.format = "JPEG"
        existing.mode = "RGB"
        existing.width = 50
        existing.height = 50
        existing.size_bytes = 1024
        existing.folder = "uploaded"
        image_service.repository.get_by_content_hash.return_value = existing

        result = image_service.upload_image(self._upload_file("copy.jpg"))

        assert result.path == "/tmp/original.jpg"
        assert result.image.filename == "original.jpg"
        image_service.repository.generate_id.assert_not_called()
        image_service.repository.create.assert_not_called()

    def test_upload_creates_new_image(self, image_service):
        image_service.repository.get_by_content_hash.return_value = None
        image_service.repository.generate_id.return_value = "new-id"
        image_service.repository.create.return_value = ImageDTO(
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

        image_service.repository.create.assert_called_once()
        assert result.image.id == "new-id"
