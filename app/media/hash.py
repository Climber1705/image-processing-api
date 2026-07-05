import hashlib
from pathlib import Path
from typing import BinaryIO

_READ_CHUNK_SIZE = 8192


def compute_checksum(source: BinaryIO) -> str:
    """Return the SHA-256 hex digest of a readable binary stream."""
    digest = hashlib.sha256()
    source.seek(0)
    while chunk := source.read(_READ_CHUNK_SIZE):
        digest.update(chunk)
    source.seek(0)
    return digest.hexdigest()


def compute_file_checksum(path: str | Path) -> str:
    """Return the SHA-256 hex digest of a file on disk."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_READ_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()
