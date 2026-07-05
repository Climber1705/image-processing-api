"""
Unit tests for image metadata helpers.
"""

import pytest
from PIL import Image
from fastapi import HTTPException

from app.media.utils.metadata import get_image_metadata


@pytest.mark.unit
class TestImageMetadata:
    """Test cases for metadata extraction functions."""

    def test_get_metadata_success(self, temp_directories, sample_image_rgb):
        """Test successful metadata extraction."""
        image_path = temp_directories["uploaded"] / "test_metadata.jpg"
        sample_image_rgb.save(image_path, format="JPEG")

        metadata = get_image_metadata(image_path)

        assert metadata.filename == "test_metadata.jpg"
        assert metadata.format == "JPEG"
        assert metadata.mode == "RGB"
        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.size_bytes > 0
        assert metadata.path == str(image_path)
        assert metadata.url is None

    def test_get_metadata_png_format(self, temp_directories):
        """Test metadata extraction for PNG format."""
        img = Image.new("RGBA", (400, 300), color=(255, 0, 0, 128))
        image_path = temp_directories["uploaded"] / "test.png"
        img.save(image_path, format="PNG")

        metadata = get_image_metadata(image_path)

        assert metadata.format == "PNG"
        assert metadata.mode == "RGBA"
        assert metadata.width == 400
        assert metadata.height == 300

    def test_get_metadata_file_not_found(self, temp_directories):
        """Test metadata extraction with non-existent file."""
        image_path = temp_directories["uploaded"] / "nonexistent.jpg"

        with pytest.raises(HTTPException) as exc_info:
            get_image_metadata(image_path)

        assert exc_info.value.status_code == 404

    def test_get_metadata_invalid_image(self, temp_directories):
        """Test metadata extraction with invalid image file."""
        image_path = temp_directories["uploaded"] / "invalid.jpg"
        image_path.write_text("not an image")

        with pytest.raises(HTTPException) as exc_info:
            get_image_metadata(image_path)

        assert exc_info.value.status_code == 500
