"""
Unit tests for vision image loading and validation.
"""

import pytest
from io import BytesIO
from PIL import Image

from app.vision.domain.errors import CorruptImageError, InvalidInputError
from app.vision.image_loader import load_from_bytes, load_from_path


@pytest.mark.unit
class TestImageLoader:
    @pytest.fixture
    def sample_jpeg_bytes(self):
        img = Image.new("RGB", (800, 600), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    def test_load_from_path_converts_to_rgb(self, temp_directories):
        image_path = temp_directories["uploaded"] / "test_valid.png"
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(image_path, format="PNG")

        loaded = load_from_path(image_path)

        assert loaded.mode == "RGB"
        assert loaded.size == (100, 100)

    def test_load_from_path_rejects_missing_file(self, temp_directories):
        image_path = temp_directories["uploaded"] / "missing.jpg"

        with pytest.raises(InvalidInputError, match="not found"):
            load_from_path(image_path)

    def test_load_from_path_rejects_empty_file(self, temp_directories):
        image_path = temp_directories["uploaded"] / "empty.jpg"
        image_path.touch()

        with pytest.raises(CorruptImageError, match="empty"):
            load_from_path(image_path)

    def test_load_from_path_rejects_corrupt_file(self, temp_directories):
        image_path = temp_directories["uploaded"] / "corrupt.jpg"
        image_path.write_text("not an image")

        with pytest.raises(CorruptImageError, match="corrupt"):
            load_from_path(image_path)

    def test_load_from_bytes_converts_to_rgb(self, sample_jpeg_bytes):
        loaded = load_from_bytes(sample_jpeg_bytes, "test.jpg")

        assert loaded.mode == "RGB"
        assert loaded.size == (800, 600)

    def test_load_from_bytes_rejects_empty(self):
        with pytest.raises(CorruptImageError, match="empty"):
            load_from_bytes(b"", "test.jpg")

    def test_load_from_bytes_rejects_corrupt(self):
        with pytest.raises(CorruptImageError, match="corrupt"):
            load_from_bytes(b"not an image", "test.jpg")
