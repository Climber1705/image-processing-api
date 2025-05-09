import os
import uuid
from pathlib import Path
from typing import Optional, Annotated
from PIL import Image, UnidentifiedImageError
from fastapi import UploadFile, HTTPException, Depends, status

from app.core.logging_config import get_logger
from app.services.image.storage.base_storage import BaseImageStorage
from app.utils.file_operations.directory_utils import DirectoryManager, get_directory_manager
from app.utils.validator.simple_validator import SimpleImageValidator, get_simple_image_validator
from app.utils.file_operations.file_utils import FilePathResolver, get_file_path_resolver

logger = get_logger("local_storage")

# Dependency injection for DirectoryManager, SimpleImageValidator, and FileFinder
DirectoryManagerDep = Annotated[DirectoryManager, Depends(get_directory_manager)]
SimpleImageValidatorDep = Annotated[SimpleImageValidator, Depends(get_simple_image_validator)]
FilePathResolverDep = Annotated[FilePathResolver, Depends(get_file_path_resolver)]


class LocalImageStorage(BaseImageStorage):
    """
    Local image storage implementation that saves, retrieves, and deletes images
    in a specified directory.
    """
    
    def __init__(self,
                 directory_manager: DirectoryManagerDep,
                 image_validator: SimpleImageValidatorDep,
                 file_resolver: FilePathResolverDep):
        """
        Initializes LocalImageStorage with required dependencies.

        @param directory_manager: Handles directory operations like fetching the correct folder paths.
        @param image_validator: Validates the image formats and extensions.
        @param file_resolver: Helps in finding a file in the local system.

        @returns: None
        """
        self.directory_manager = directory_manager
        self.image_verifier = image_validator
        self.file_resolver = file_resolver

    def _get_file_name(self, filename: Optional[str], format: str = "JPEG") -> str:
        """
        Generate a unique filename for the image.

        @param filename: Optional filename provided by the user.
        @param format: The desired format for the image (default is "JPEG").

        @returns: A valid file name with the appropriate extension.
        """
        # Validate and retrieve the correct extension for the image format.
        format = self.image_verifier.validate_format(format)
        ext = self.image_verifier.get_extension(format)

        # If no filename provided, generate a random one with the correct extension.
        if filename is None:
            return f"{uuid.uuid4()}{ext}"

        # Remove the extension from the provided filename and append the validated extension.
        filename = Path(filename).stem  # Remove the extension
        return f"{filename}{ext}"

    def save(self, file: UploadFile, folder: Optional[str] = "uploaded", filename: Optional[str] = None, format: str = "JPEG") -> str:
        """
        Save an uploaded image to the local storage.

        @param file: The image file uploaded by the user.
        @param folder: The folder where the image will be saved (default is "uploaded").
        @param filename: The optional name to save the file as.
        @param format: The format to save the file as (default is "JPEG").

        @returns: The storage path (URL) of the saved image.
        """
        # Get the final file name to use.
        filename = self._get_file_name(filename, format)
        directory = self.directory_manager.get_directory(folder)
        file_path = directory / filename

        try:
            # Try to open and save the image.
            with Image.open(file.file) as img:
                img.save(file_path, format=format.upper())
            logger.info(f"Saved image: {file_path}")
            return str(file_path)

        except UnidentifiedImageError:
            # If the file is not a valid image, remove the invalid file and raise an error.
            if file_path.exists():
                os.remove(file_path)
            logger.error(f"Uploaded file is not a valid image: {file_path}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is not a valid image")

        except Exception as e:
            # If there's an error saving the image, remove the invalid file and log the error.
            if file_path.exists():
                os.remove(file_path)
            logger.error(f"Failed to save image {file_path}: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save image")

    def get_url(self, filename: str) -> str:
        """
        Get the URL for a saved image.

        @param filename: The name of the file for which the URL is needed.

        @returns: The URL or path to the file.
        """
        url = self.file_resolver.find_file(filename=filename)
        return url

    def delete(self, directory: str, filename: str) -> bool:
        """
        Delete a file from the local storage.

        @param directory: The folder where the image is located.
        @param filename: The name of the image to delete.

        @returns: True if the file was deleted successfully, False otherwise.
        """
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
    file_resolver: FilePathResolverDep
) -> LocalImageStorage:
    """
    Dependency injection function to get an instance of LocalImageStorage.

    @param directory_manager: Handles directory-related operations.
    @param image_validator: Validates the image formats.
    @param file_resolver: Helps to find files in the storage.

    @returns: An instance of LocalImageStorage.
    """
    return LocalImageStorage(
        directory_manager=directory_manager,
        image_validator=image_validator,
        file_resolver=file_resolver
    )
