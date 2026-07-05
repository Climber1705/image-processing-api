import hashlib
from pathlib import Path
from typing import BinaryIO

_CHUNK_SIZE = 8192


def stream_sha256(source: BinaryIO) -> str:
    digest = hashlib.sha256()
    source.seek(0)
    while chunk := source.read(_CHUNK_SIZE):
        digest.update(chunk)
    source.seek(0)
    return digest.hexdigest()


def compute_checksum(source: BinaryIO) -> str:
    """SHA-256 hex digest of a readable binary stream."""
    return stream_sha256(source)


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()
