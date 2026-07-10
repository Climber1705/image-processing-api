import os
import shutil
from pathlib import Path
from typing import BinaryIO

from PIL import Image, UnidentifiedImageError

from app.core.logging_config import get_logger
from app.storage.base_storage import BaseImageStorage
from app.storage.directories import DirectoryManager
from app.storage.errors import InvalidImageFileError, StorageOperationError
from app.validation.validator import get_format_extension, validate_image_format

logger = get_logger("local_storage")


class LocalImageStorage(BaseImageStorage):
    def __init__(
        self,
        directories: dict[str, Path],
        format_extensions: dict[str, str],
    ):
        self._dirs = DirectoryManager(directories)
        self._format_extensions = format_extensions

    def _resolve_under_folder(self, folder: str, *parts: str) -> Path:
        """Join path parts under a folder and reject any escape outside it."""
        base = self._dirs.get_directory(folder).resolve()
        candidate = base.joinpath(*parts).resolve()
        if not candidate.is_relative_to(base):
            raise StorageOperationError("Resolved path escapes storage directory")
        return candidate

    def destination_path(self, source: str | Path, target_folder: str) -> Path:
        return self._resolve_under_folder(target_folder, Path(source).name)

    def exists(self, path: str | Path) -> bool:
        return Path(path).is_file()

    def save(
        self,
        file: BinaryIO,
        folder: str,
        storage_id: str,
        format: str = "JPEG",
        display_filename: str | None = None,
    ) -> str:
        validated_format = validate_image_format(format, self._format_extensions)
        ext = get_format_extension(validated_format, self._format_extensions)
        if display_filename is not None:
            safe_name = Path(display_filename).name
            file_path = self._resolve_under_folder(folder, storage_id, safe_name)
        else:
            file_path = self._resolve_under_folder(folder, f"{storage_id}{ext}")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            pillow_format = "JPEG" if validated_format.upper() == "JPG" else validated_format.upper()
            with Image.open(file) as img:
                img.save(file_path, format=pillow_format)
            return str(file_path)

        except UnidentifiedImageError as exc:
            if file_path.exists():
                os.remove(file_path)
            logger.error("Uploaded file is not a valid image: %s", file_path)
            raise InvalidImageFileError("Uploaded file is not a valid image") from exc

        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            logger.error("Failed to save image %s: %s", file_path, e)
            raise StorageOperationError("Failed to save image") from e

    def read(self, path: str | Path) -> BinaryIO:
        file_path = Path(path)
        if not file_path.is_file():
            raise FileNotFoundError(file_path)
        return open(file_path, "rb")

    def delete(self, path: str | Path) -> bool:
        file_path = Path(path)
        try:
            os.remove(file_path)
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error("Error deleting file %s: %s", file_path, e)
            return False

    def move(self, source: str | Path, target_folder: str) -> str:
        source_path = Path(source)
        dest_path = self.destination_path(source_path, target_folder)
        shutil.move(str(source_path), str(dest_path))
        return str(dest_path)
