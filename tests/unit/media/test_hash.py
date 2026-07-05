"""
Unit tests for image content hashing.
"""

import pytest
from io import BytesIO
from pathlib import Path

from app.media.hash import file_sha256, stream_sha256


@pytest.mark.unit
class TestImageHash:
    def test_stream_sha256_is_deterministic(self):
        data = b"same-image-bytes"
        assert stream_sha256(BytesIO(data)) == stream_sha256(BytesIO(data))

    def test_stream_sha256_resets_position(self):
        source = BytesIO(b"reset-me")
        stream_sha256(source)
        assert source.tell() == 0

    def test_file_sha256_matches_stream(self, temp_directories):
        path = temp_directories["uploaded"] / "hash_test.bin"
        path.write_bytes(b"file-content-for-hash")

        assert file_sha256(path) == stream_sha256(BytesIO(path.read_bytes()))

    def test_file_sha256_differs_for_different_files(self, temp_directories):
        first = temp_directories["uploaded"] / "first.bin"
        second = temp_directories["uploaded"] / "second.bin"
        first.write_bytes(b"one")
        second.write_bytes(b"two")

        assert file_sha256(first) != file_sha256(second)
