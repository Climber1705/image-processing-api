import os
from pathlib import Path
from collections.abc import Iterable

from app.core.logging_config import get_logger
from app.storage.errors import InvalidStorageFolderError, StorageOperationError

logger = get_logger("directories")


def storage_dirs_writable(directories: Iterable[Path]) -> bool:
    for path in directories:
        if not path.exists() or not path.is_dir():
            return False
        if not os.access(path, os.W_OK):
            return False
    return True


class DirectoryManager:
    def __init__(self, directories: dict[str, Path]):
        self.directories = directories
        self._create_directories()

    def _create_directories(self) -> None:
        for directory in self.directories.values():
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Error creating directory %s: %s", directory, e)
                raise StorageOperationError(
                    f"Failed to create directory: {directory}. Error: {e}",
                ) from e

    def validate_folder(self, folder: str) -> bool:
        return folder in self.directories

    def get_directory(self, folder: str) -> Path:
        if not self.validate_folder(folder):
            raise InvalidStorageFolderError(f"Invalid folder: {folder}")
        return self.directories[folder]
