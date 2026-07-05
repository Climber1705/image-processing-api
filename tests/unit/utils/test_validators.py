"""
Unit tests for SimpleImageValidator utility.
"""

import pytest
from io import BytesIO
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.validation.simple_validator import SimpleImageValidator


@pytest.mark.unit
class TestSimpleImageValidator:
    """Test cases for SimpleImageValidator."""

    @pytest.fixture
    def validator(self, format_extensions):
        """Create SimpleImageValidator with format extensions."""
        return SimpleImageValidator(
            format_extensions=format_extensions,
            max_size_mb=5,
            allowed_types=("image/jpeg", "image/png")
        )

    def test_validate_success(self, validator, valid_upload_file):
        """Test successful validation."""
        validator.validate(valid_upload_file)

    def test_validate_type_success(self, validator):
        """Test successful type validation."""
        valid_file = UploadFile(
            filename="test.jpg",
            file=BytesIO(b"fake content"),
            headers={"content-type": "image/jpeg"}
        )
        
        validator.validate_type(valid_file)

    def test_validate_type_invalid(self, validator):
        """Test type validation with invalid MIME type."""
        invalid_file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"fake content"),
            headers={"content-type": "text/plain"}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_type(invalid_file)
        
        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    def test_validate_size_success(self, validator):
        """Test successful size validation."""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        valid_file = UploadFile(
            filename="test.jpg",
            file=img_bytes,
            headers={"content-type": "image/jpeg"}
        )
        
        validator.validate_size(valid_file)

    def test_validate_size_too_large(self, validator):
        """Test size validation with file exceeding limit."""
        large_content = b"x" * (6 * 1024 * 1024)
        large_file = UploadFile(
            filename="large.jpg",
            file=BytesIO(large_content),
            headers={"content-type": "image/jpeg"}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_size(large_file)
        
        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail.lower() or "File too large" in exc_info.value.detail

    def test_validate_format_success(self, validator):
        """Test successful format validation."""
        formats = ["JPEG", "PNG", "GIF", "BMP"]
        
        for fmt in formats:
            result = validator.validate_format(fmt)
            assert result == fmt.upper()

    def test_validate_format_invalid(self, validator):
        """Test format validation with invalid format."""
        with pytest.raises(HTTPException) as exc_info:
            validator.validate_format("INVALID")
        
        assert exc_info.value.status_code == 400
        assert "Unsupported image format" in exc_info.value.detail

    def test_validate_format_case_insensitive(self, validator):
        """Test format validation is case insensitive."""
        result1 = validator.validate_format("jpeg")
        result2 = validator.validate_format("JPEG")
        result3 = validator.validate_format("Jpeg")
        
        assert result1 == "JPEG"
        assert result2 == "JPEG"
        assert result3 == "JPEG"

    def test_get_extension_success(self, validator):
        """Test getting extension for valid format."""
        extensions = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif"
        }
        
        for format_name, expected_ext in extensions.items():
            result = validator.get_extension(format_name)
            assert result == expected_ext

    def test_get_extension_invalid_format(self, validator):
        """Test getting extension for invalid format."""
        with pytest.raises(HTTPException):
            validator.get_extension("INVALID")