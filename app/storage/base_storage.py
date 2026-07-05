from pathlib import Path
from typing import BinaryIO
from abc import ABC, abstractmethod


class BaseImageStorage(ABC):
    @abstractmethod
    def save(
        self,
        file: BinaryIO,
        folder: str,
        storage_id: str,
        format: str = "JPEG",
        *,
        display_filename: str | None = None,
    ) -> str:
        """Write bytes to disk. Returns absolute path string."""

    @abstractmethod
    def read(self, path: str | Path) -> BinaryIO:
        """Open existing file for reading."""

    @abstractmethod
    def delete(self, path: str | Path) -> bool:
        """Delete file at path. Returns False if already gone."""

    @abstractmethod
    def move(self, source: str | Path, target_folder: str) -> str:
        """Move file to another folder. Returns new absolute path."""

    @abstractmethod
    def exists(self, path: str | Path) -> bool:
        """Return True if the file exists at path."""

    @abstractmethod
    def destination_path(self, source: str | Path, target_folder: str) -> Path:
        """Return the filesystem path a move would target."""
