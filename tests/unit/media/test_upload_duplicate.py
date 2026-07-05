"""
Unit tests for duplicate upload detection.
"""

from io import BytesIO
from unittest.mock import Mock

import pytest
from app.media.domain.dtos import ImageDTO
from app.media.service import ImageService
from app.storage.local_storage import LocalImageStorage
from PIL import Image


@pytest.mark.unit
class TestDuplicateUpload:
    @pytest.fixture
    def image_service(self, temp_directories, test_settings, format_extensions):
        return ImageService(
            settings=test_settings,
            repository=Mock(),
            storage=LocalImageStorage(
                directories=temp_directories,
                format_extensions=format_extensions,
            ),
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
        image_service.repository.create.assert_not_called()

    def test_upload_creates_new_image(self, image_service):
        image_service.repository.get_by_content_hash.return_value = None
        image_service.repository.create.return_value = ImageDTO(
            id="new-id",
            filename="photo.jpg",
            format="JPEG",
            mode="RGB",
            width=50,
            height=50,
            size_bytes=1024,
            path=str(image_service.settings.UPLOADED_FOLDER / "new-id.jpg"),
            folder="uploaded",
        )

        result = image_service.upload_image(self._upload_file("photo.jpg"))

        image_service.repository.create.assert_called_once()
        assert result.image.id == "new-id"
