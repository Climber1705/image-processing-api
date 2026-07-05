import os
import uuid
from typing import BinaryIO
from pathlib import Path
from fastapi import HTTPException, status
from PIL import Image, UnidentifiedImageError

from app.core.logging_config import get_logger
from app.storage.base_storage import BaseImageStorage
from app.media.utils.directory_utils import DirectoryManager
from app.media.utils.validator.simple_validator import SimpleImageValidator
from app.media.utils.file_utils import FilePathResolver

logger = get_logger("local_storage")


class LocalImageStorage(BaseImageStorage):
    def __init__(
        self,
        directory_manager: DirectoryManager,
        image_validator: SimpleImageValidator,
        file_resolver: FilePathResolver,
    ):
        self.directory_manager = directory_manager
        self.image_verifier = image_validator
        self.file_resolver = file_resolver

    def _get_storage_filename(self, storage_id: str | None, format: str = "JPEG") -> tuple[str, str]:
        format = self.image_verifier.validate_format(format)
        ext = self.image_verifier.get_extension(format)
        storage_id = storage_id or str(uuid.uuid4())
        return storage_id, f"{storage_id}{ext}"

    def save(
        self,
        file: BinaryIO,
        folder: str | None = "uploaded",
        storage_id: str | None = None,
        format: str = "JPEG",
    ) -> str:
        storage_id, filename = self._get_storage_filename(storage_id, format)
        directory = self.directory_manager.get_directory(folder)
        file_path = directory.joinpath(filename)

        try:
            with Image.open(file) as img:
                img.save(file_path, format=format.upper())
            logger.info(f"Saved image: {file_path}")
            return str(file_path)

        except UnidentifiedImageError:
            if file_path.exists():
                os.remove(file_path)
            logger.error(f"Uploaded file is not a valid image: {file_path}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is not a valid image")

        except Exception as e:
            if file_path.exists():
                os.remove(file_path)
            logger.error(f"Failed to save image {file_path}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save image")

    def get(self, filename: str) -> BinaryIO:
        file_path = self.file_resolver.find_file(filename=filename)
        return open(file_path, "rb")

    def delete(self, filename: str) -> bool:
        file_path = self.file_resolver.find_file(filename=filename)

        try:
            os.remove(file_path)
            logger.info(f"Deleted image: {file_path}")
            return True
        except FileNotFoundError:
            logger.warning(f"Tried to delete missing file: {file_path}")
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
