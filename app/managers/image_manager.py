import logging
from typing import Dict, List, Optional, Annotated
from pathlib import Path
from fastapi import UploadFile, Depends

from app.utils.file_operations.directory_utils import DirectoryManager, get_directory_manager
from app.services.image.storage.local_storage import LocalImageStorage, get_local_image_storage
from app.services.image.crud_operations import ImageCRUDService, get_image_crud_service
from app.services.image.metadata_handler import ImageMetadataExtractor, get_image_metadata_extractor
from app.core.logging_config import get_logger

# Initialize logger
logger = get_logger("image_manager")

DirectoryManagerDep = Annotated[DirectoryManager, Depends(get_directory_manager)]
LocalImageStorageDep = Annotated[LocalImageStorage, Depends(get_local_image_storage)]
ImageCRUDServiceDep = Annotated[ImageCRUDService, Depends(get_image_crud_service)]
ImageMetadataExtractorDep = Annotated[ImageMetadataExtractor, Depends(get_image_metadata_extractor)]

class ImageManager:
    def __init__(
        self,
        directory_manager: DirectoryManagerDep,
        local_storage: LocalImageStorageDep,
        image_CRUD: ImageCRUDServiceDep,
        metadata_extractor: ImageMetadataExtractorDep
    ):
        """
        Initializes the ImageManager with necessary services.

        @param directory_manager: Manages directory paths and folder operations.
        @param local_storage: Handles file saving and storage.
        @param image_CRUD: Handles database CRUD operations for images.
        @param metadata_extractor: Extracts metadata from images.
        """
        self.directory_manager = directory_manager
        self.local_storage = local_storage
        self.image_CRUD = image_CRUD
        self.metadata_extractor = metadata_extractor

    def save_uploaded_image(self, file: UploadFile, filename: Optional[str] = None, format: str = "JPEG") -> str:
        """
        Saves an uploaded image file to local storage.

        @param file: The uploaded image file.
        @param filename: Optional custom filename.
        @param format: Image format (default is JPEG).
        @return: Path to the saved image file.
        """
        logger.info(f"Saving uploaded image: {filename or file.filename}")
        return self.local_storage.save(file=file, folder="uploaded", filename=filename, format=format)

    def get_image_path(self, image_name: str, folder: str = "uploaded") -> str:
        """
        Retrieves the full path of an image by its name.

        @param image_name: Name of the image file.
        @param folder: Folder where the image is stored.
        @return: Path to the image file.
        """
        logger.debug(f"Getting image path for: {image_name} in folder: {folder}")
        image_path = self.image_CRUD.get_image_path(image_name, folder)
        return str(image_path)

    def get_image_dimensions(self, image_path: Path) -> tuple[int, int]:
        """
        Retrieves the width and height of the image.

        @param image_path: Path to the image file.
        @return: Tuple containing width and height.
        """
        logger.debug(f"Getting image dimensions for: {image_path}")
        return self.metadata_extractor.get_dimensions(image_path)

    def get_image_metadata(self, image_path: Path) -> Dict:
        """
        Retrieves metadata from an image file.

        @param image_path: Path to the image file.
        @return: Dictionary of extracted metadata.
        """
        logger.debug(f"Getting metadata for image: {image_path}")
        return self.metadata_extractor.get_metadata(image_path)

    def get_image_by_id(self, image_id: str, folder: str = "uploaded") -> Dict:
        """
        Retrieves image information by its ID.

        @param image_id: Unique identifier for the image.
        @param folder: Folder where the image is stored.
        @return: Dictionary containing image data.
        """
        logger.debug(f"Getting image by ID: {image_id}")
        return self.image_CRUD.get_image_by_id(image_id, folder)

    def list_images(self, folder: str = "uploaded", limit: int = 100, offset: int = 0, subdirectory: Optional[str] = None) -> List[Dict]:
        """
        Lists images in a folder with optional pagination and subdirectory filtering.

        @param folder: Folder to search in.
        @param limit: Max number of images to return.
        @param offset: Number of images to skip.
        @param subdirectory: Optional subfolder name.
        @return: List of image metadata dictionaries.
        """
        logger.debug(f"Listing images in folder: {folder}, subdirectory: {subdirectory}")
        return self.image_CRUD.list_images(folder, limit, offset, subdirectory)

    def delete_image(self, image_id: str, folder: str = "uploaded") -> Dict:
        """
        Deletes a single image by ID.

        @param image_id: Unique identifier for the image.
        @param folder: Folder from which to delete the image.
        @return: Dictionary confirming deletion.
        """
        logger.info(f"Deleting image with ID: {image_id} from folder: {folder}")
        return self.image_CRUD.delete_image(image_id, folder)

    def delete_all_images(self, folder: str) -> Dict:
        """
        Deletes all images in a specified folder.

        @param folder: Folder to delete all images from.
        @return: Dictionary summarizing the deletion result.
        """
        logger.warning(f"Deleting all images in folder: {folder}")
        return self.image_CRUD.delete_all_images(folder)

    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> Dict:
        """
        Moves an image from one folder to another.

        @param image_id: Unique identifier for the image.
        @param source_folder: Folder to move the image from.
        @param target_folder: Folder to move the image to.
        @return: Dictionary confirming the move.
        """
        logger.info(f"Moving image {image_id} from {source_folder} to {target_folder}")
        return self.image_CRUD.move_image(image_id, source_folder, target_folder)


def get_image_manager(
    directory_manager: DirectoryManagerDep,
    local_storage: LocalImageStorageDep,
    image_CRUD: ImageCRUDServiceDep,
    metadata_extractor: ImageMetadataExtractorDep
) -> ImageManager:
    """
    Dependency injector for ImageManager.

    @param directory_manager: DirectoryManager dependency.
    @param local_storage: LocalImageStorage dependency.
    @param image_CRUD: ImageCRUDService dependency.
    @param metadata_extractor: ImageMetadataExtractor dependency.
    @return: Instance of ImageManager.
    """
    return ImageManager(
        directory_manager=directory_manager,
        local_storage=local_storage,
        image_CRUD=image_CRUD,
        metadata_extractor=metadata_extractor
    )
