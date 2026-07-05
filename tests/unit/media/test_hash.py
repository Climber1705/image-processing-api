"""
Unit tests for image content hashing.
"""

import pytest
from io import BytesIO
from pathlib import Path

from app.media.hash import compute_checksum, compute_file_checksum


@pytest.mark.unit
class TestImageHash:
    def test_compute_checksum_is_deterministic(self):
        data = b"same-image-bytes"
        assert compute_checksum(BytesIO(data)) == compute_checksum(BytesIO(data))

    def test_compute_checksum_resets_position(self):
        source = BytesIO(b"reset-me")
        compute_checksum(source)
        assert source.tell() == 0

    def test_compute_file_checksum_matches_stream(self, temp_directories):
        path = temp_directories["uploaded"] / "hash_test.bin"
        path.write_bytes(b"file-content-for-hash")

        assert compute_file_checksum(path) == compute_checksum(BytesIO(path.read_bytes()))

    def test_compute_file_checksum_differs_for_different_files(self, temp_directories):
        first = temp_directories["uploaded"] / "first.bin"
        second = temp_directories["uploaded"] / "second.bin"
        first.write_bytes(b"one")
        second.write_bytes(b"two")

        assert compute_file_checksum(first) != compute_file_checksum(second)
