"""Unit tests for filename sanitization helpers."""

import pytest
from app.media.domain.errors import InvalidFilenameError
from app.media.utils.filename import (
    build_display_filename,
    get_display_filename,
    sanitize_filename,
)


@pytest.mark.unit
class TestFilenameSanitization:
    def test_sanitize_strips_directory_components(self):
        assert sanitize_filename("../escape.jpg") == "escape.jpg"
        assert sanitize_filename("foo/bar.png") == "bar.png"

    def test_sanitize_rejects_empty_and_dot_names(self):
        with pytest.raises(InvalidFilenameError):
            sanitize_filename("..")
        with pytest.raises(InvalidFilenameError):
            sanitize_filename(".")
        with pytest.raises(InvalidFilenameError):
            sanitize_filename("")

    def test_get_display_filename_uses_safe_stem(self):
        assert get_display_filename("../evil", None, ".jpg") == "evil.jpg"
        assert get_display_filename(None, "dir/photo.PNG", ".jpg") == "photo.jpg"

    def test_build_display_filename_with_suffix(self):
        assert build_display_filename("photo.jpg", "resized") == "photo_resized.jpg"
        assert build_display_filename("../photo.jpg", "gray") == "photo_gray.jpg"
