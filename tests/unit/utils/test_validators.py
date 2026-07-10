"""
Unit tests for image validation utilities.
"""

from io import BytesIO

import pytest
from app.validation.validator import (
    allowed_mime_types_for_formats,
    default_allowed_mime_types,
    get_format_extension,
    validate_image_format,
    validate_image_size,
    validate_image_type,
    validate_upload,
)
from fastapi import HTTPException, UploadFile
from PIL import Image


@pytest.mark.unit
class TestImageValidation:
    """Test cases for image validation functions."""

    @pytest.fixture
    def allowed_types(self, format_extensions):
        return allowed_mime_types_for_formats(format_extensions)

    def test_default_allowed_mime_types_match_format_extensions(self, format_extensions):
        """Upload MIME allowlist covers every configured output format."""
        mimes = default_allowed_mime_types()
        expected = allowed_mime_types_for_formats(format_extensions)
        assert mimes == expected
        assert "image/webp" in mimes
        assert "image/gif" in mimes

    def test_validate_webp_upload_success(self, format_extensions):
        """WEBP uploads are accepted when listed in FORMAT_EXTENSIONS."""
        webp_file = UploadFile(
            filename="test.webp",
            file=BytesIO(b"fake content"),
            headers={"content-type": "image/webp"},
        )
        validate_image_type(
            webp_file,
            allowed_mime_types_for_formats(format_extensions),
        )

    def test_validate_upload_success(self, valid_upload_file):
        """Test successful validation."""
        validate_upload(valid_upload_file)

    def test_validate_type_success(self, allowed_types):
        """Test successful type validation."""
        valid_file = UploadFile(
            filename="test.jpg",
            file=BytesIO(b"fake content"),
            headers={"content-type": "image/jpeg"},
        )

        validate_image_type(valid_file, allowed_types)

    def test_validate_type_invalid(self, allowed_types):
        """Test type validation with invalid MIME type."""
        invalid_file = UploadFile(
            filename="test.txt",
            file=BytesIO(b"fake content"),
            headers={"content-type": "text/plain"},
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_image_type(invalid_file, allowed_types)

        assert exc_info.value.status_code == 400
        assert "Unsupported file type" in exc_info.value.detail

    def test_validate_size_success(self):
        """Test successful size validation."""
        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        valid_file = UploadFile(
            filename="test.jpg",
            file=img_bytes,
            headers={"content-type": "image/jpeg"},
        )

        validate_image_size(valid_file, max_size_bytes=5 * 1024 * 1024)

    def test_validate_size_too_large(self):
        """Test size validation with file exceeding limit."""
        large_content = b"x" * (6 * 1024 * 1024)
        large_file = UploadFile(
            filename="large.jpg",
            file=BytesIO(large_content),
            headers={"content-type": "image/jpeg"},
        )

        with pytest.raises(HTTPException) as exc_info:
            validate_image_size(large_file, max_size_bytes=5 * 1024 * 1024)

        assert exc_info.value.status_code == 400
        assert "too large" in exc_info.value.detail.lower() or "File too large" in exc_info.value.detail

    def test_validate_format_success(self, format_extensions):
        """Test successful format validation."""
        formats = ["JPEG", "PNG", "GIF", "BMP"]

        for fmt in formats:
            result = validate_image_format(fmt, format_extensions)
            assert result == fmt.upper()

    def test_validate_format_invalid(self, format_extensions):
        """Test format validation with invalid format."""
        with pytest.raises(HTTPException) as exc_info:
            validate_image_format("INVALID", format_extensions)

        assert exc_info.value.status_code == 400
        assert "Unsupported image format" in exc_info.value.detail

    def test_validate_format_case_insensitive(self, format_extensions):
        """Test format validation is case insensitive."""
        result1 = validate_image_format("jpeg", format_extensions)
        result2 = validate_image_format("JPEG", format_extensions)
        result3 = validate_image_format("Jpeg", format_extensions)

        assert result1 == "JPEG"
        assert result2 == "JPEG"
        assert result3 == "JPEG"

    def test_get_extension_success(self, format_extensions):
        """Test getting extension for valid format."""
        extensions = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif",
        }

        for format_name, expected_ext in extensions.items():
            result = get_format_extension(format_name, format_extensions)
            assert result == expected_ext

    def test_get_extension_invalid_format(self, format_extensions):
        """Test getting extension for invalid format."""
        with pytest.raises(HTTPException):
            get_format_extension("INVALID", format_extensions)
