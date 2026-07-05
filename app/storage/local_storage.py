import os
import shutil
from typing import BinaryIO
from pathlib import Path
from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.logging_config import get_logger
from app.storage.base_storage import BaseImageStorage
from app.storage.directories import DirectoryManager
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

    def destination_path(self, source: str | Path, target_folder: str) -> Path:
        return self._dirs.get_directory(target_folder) / Path(source).name

    def exists(self, path: str | Path) -> bool:
        return Path(path).is_file()

    def save(
        self,
        file: BinaryIO,
        folder: str,
        storage_id: str,
        format: str = "JPEG",
        *,
        display_filename: str | None = None,
    ) -> str:
        validated_format = validate_image_format(format, self._format_extensions)
        ext = get_format_extension(validated_format, self._format_extensions)
        if display_filename is not None:
            file_path = self._dirs.get_directory(folder) / storage_id / display_filename
        else:
            file_path = self._dirs.get_directory(folder) / f"{storage_id}{ext}"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with Image.open(file) as img:
                img.save(file_path, format=validated_format.upper())
            return str(file_path)

        except UnidentifiedImageError:
            if file_path.exists():
                os.remove(file_path)
            logger.error("Uploaded file is not a valid image: %s", file_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is not a valid image")

        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            logger.error("Failed to save image %s: %s", file_path, e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save image")

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
