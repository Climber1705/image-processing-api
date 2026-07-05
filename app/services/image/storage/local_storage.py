from fastapi import UploadFile, HTTPException, Depends, status
from PIL import Image, UnidentifiedImageError
from typing import Optional, Annotated
from pathlib import Path
import uuid
import os

from app.core.logging_config import get_logger
from app.services.image.storage.base_storage import BaseImageStorage
from app.utils.file_operations.directory_utils import DirectoryManager, get_directory_manager
from app.utils.validator.simple_validator import SimpleImageValidator, get_simple_image_validator
from app.utils.file_operations.file_utils import FilePathResolver, get_file_path_resolver

logger = get_logger("local_storage")

DirectoryManagerDep = Annotated[DirectoryManager, Depends(get_directory_manager)]
SimpleImageValidatorDep = Annotated[SimpleImageValidator, Depends(get_simple_image_validator)]
FilePathResolverDep = Annotated[FilePathResolver, Depends(get_file_path_resolver)]


class LocalImageStorage(BaseImageStorage):
    def __init__(
        self,
        directory_manager: DirectoryManagerDep,
        image_validator: SimpleImageValidatorDep,
        file_resolver: FilePathResolverDep,
    ):
        self.directory_manager = directory_manager
        self.image_verifier = image_validator
        self.file_resolver = file_resolver

    def _get_file_name(self, filename: Optional[str], format: str = "JPEG") -> str:
        format = self.image_verifier.validate_format(format)
        ext = self.image_verifier.get_extension(format)

        if filename is None:
            return f"{uuid.uuid4()}{ext}"

        filename = Path(filename).stem
        return f"{filename}{ext}"

    def save(
        self,
        file: UploadFile,
        folder: Optional[str] = "uploaded",
        filename: Optional[str] = None,
        format: str = "JPEG",
    ) -> str:
        filename = self._get_file_name(filename, format)
        directory = self.directory_manager.get_directory(folder)
        file_path = directory / filename

        try:
            with Image.open(file.file) as img:
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

    def get_url(self, filename: str) -> str:
        return self.file_resolver.find_file(filename=filename)

    def delete(self, directory: str, filename: str) -> bool:
        directory = self.directory_manager.get_directory(directory)
        file_path = directory / filename

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


def get_local_image_storage(
    directory_manager: DirectoryManagerDep,
    image_validator: SimpleImageValidatorDep,
    file_resolver: FilePathResolverDep,
) -> LocalImageStorage:
    return LocalImageStorage(
        directory_manager=directory_manager,
        image_validator=image_validator,
        file_resolver=file_resolver,
    )
