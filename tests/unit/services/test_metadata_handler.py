"""
Unit tests for ImageMetadataExtractor service.
"""

import pytest
from PIL import Image
from fastapi import HTTPException

from app.media.metadata_handler import ImageMetadataExtractor


@pytest.mark.unit
class TestImageMetadataExtractor:
    """Test cases for ImageMetadataExtractor."""

    def test_get_dimensions_success(self, temp_directories, sample_image_rgb):
        """Test successful dimension extraction."""
        image_path = temp_directories["uploaded"] / "test.jpg"
        sample_image_rgb.save(image_path, format="JPEG")
        
        width, height = ImageMetadataExtractor.get_dimensions(image_path)
        
        assert width == 800
        assert height == 600

    def test_get_dimensions_different_sizes(self, temp_directories):
        """Test dimension extraction for different image sizes."""
        sizes = [(100, 100), (1920, 1080), (50, 200)]
        
        for width, height in sizes:
            image_path = temp_directories["uploaded"] / f"test_{width}x{height}.jpg"
            img = Image.new('RGB', (width, height), color='blue')
            img.save(image_path, format="JPEG")
            
            extracted_width, extracted_height = ImageMetadataExtractor.get_dimensions(image_path)
            
            assert extracted_width == width
            assert extracted_height == height

    def test_get_dimensions_file_not_found(self, temp_directories):
        """Test dimension extraction with non-existent file."""
        image_path = temp_directories["uploaded"] / "nonexistent.jpg"
        
        with pytest.raises(HTTPException) as exc_info:
            ImageMetadataExtractor.get_dimensions(image_path)
        
        assert exc_info.value.status_code == 500

    def test_get_metadata_success(self, temp_directories, sample_image_rgb):
        """Test successful metadata extraction."""
        image_path = temp_directories["uploaded"] / "test_metadata.jpg"
        sample_image_rgb.save(image_path, format="JPEG")
        
        metadata = ImageMetadataExtractor.get_metadata(image_path)
        
        assert metadata["filename"] == "test_metadata.jpg"
        assert metadata["format"] == "JPEG"
        assert metadata["mode"] == "RGB"
        assert metadata["width"] == 800
        assert metadata["height"] == 600
        assert metadata["size_bytes"] > 0
        assert metadata["path"] == str(image_path)
        assert metadata["url"] is None

    def test_get_metadata_png_format(self, temp_directories):
        """Test metadata extraction for PNG format."""
        image_path = temp_directories["uploaded"] / "test.png"
        img = Image.new('RGBA', (400, 300), color=(255, 0, 0, 128))
        img.save(image_path, format="PNG")
        
        metadata = ImageMetadataExtractor.get_metadata(image_path)
        
        assert metadata["format"] == "PNG"
        assert metadata["mode"] == "RGBA"
        assert metadata["width"] == 400
        assert metadata["height"] == 300

    def test_get_metadata_file_not_found(self, temp_directories):
        """Test metadata extraction with non-existent file."""
        image_path = temp_directories["uploaded"] / "nonexistent.jpg"
        
        with pytest.raises(HTTPException) as exc_info:
            ImageMetadataExtractor.get_metadata(image_path)
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_get_metadata_invalid_image(self, temp_directories):
        """Test metadata extraction with invalid image file."""
        image_path = temp_directories["uploaded"] / "invalid.jpg"
        image_path.write_text("not an image")
        
        with pytest.raises(HTTPException) as exc_info:
            ImageMetadataExtractor.get_metadata(image_path)
        
        assert exc_info.value.status_code == 500