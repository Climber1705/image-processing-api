from typing import Dict, List, Optional, Annotated, Tuple, Any
from fastapi import UploadFile, Depends
from pathlib import Path

from app.utils.file_operations.directory_utils import DirectoryManager, get_directory_manager
from app.services.image.storage.local_storage import LocalImageStorage, get_local_image_storage
from app.services.image.crud_operations import ImageCRUDService, get_image_crud_service
from app.services.image.metadata_handler import ImageMetadataExtractor, get_image_metadata_extractor
from app.core.logging_config import get_logger

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
        metadata_extractor: ImageMetadataExtractorDep,
    ):
        self.directory_manager = directory_manager
        self.local_storage = local_storage
        self.image_CRUD = image_CRUD
        self.metadata_extractor = metadata_extractor

    def save_uploaded_image(self, file: UploadFile, filename: Optional[str] = None, format: str = "JPEG") -> str:
        logger.info(f"Saving uploaded image: {filename or file.filename}")
        return self.local_storage.save(file=file, folder="uploaded", filename=filename, format=format)

    def get_image_path(self, image_name: str, folder: str = "uploaded") -> str:
        logger.debug(f"Getting image path for: {image_name} in folder: {folder}")
        return str(self.image_CRUD.get_image_path(image_name, folder))

    def get_image_dimensions(self, image_path: Path) -> Tuple[int, int]:
        logger.debug(f"Getting image dimensions for: {image_path}")
        return self.metadata_extractor.get_dimensions(image_path)

    def get_image_metadata(self, image_path: Path) -> Dict[str, Any]:
        logger.debug(f"Getting metadata for image: {image_path}")
        return self.metadata_extractor.get_metadata(image_path)

    def get_image_by_id(self, image_id: str, folder: str = "uploaded") -> Dict[str, Any]:
        logger.debug(f"Getting image by ID: {image_id}")
        return self.image_CRUD.get_image_by_id(image_id, folder)

    def list_images(
        self,
        folder: str = "uploaded",
        limit: int = 100,
        offset: int = 0,
        subdirectory: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        logger.debug(f"Listing images in folder: {folder}, subdirectory: {subdirectory}")
        return self.image_CRUD.list_images(folder, limit, offset, subdirectory)

    def delete_image(self, image_id: str, folder: str = "uploaded") -> Dict[str, Any]:
        logger.info(f"Deleting image with ID: {image_id} from folder: {folder}")
        return self.image_CRUD.delete_image(image_id, folder)

    def delete_all_images(self, folder: str) -> Dict[str, str]:
        logger.warning(f"Deleting all images in folder: {folder}")
        return self.image_CRUD.delete_all_images(folder)

    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> Dict[str, Any]:
        logger.info(f"Moving image {image_id} from {source_folder} to {target_folder}")
        return self.image_CRUD.move_image(image_id, source_folder, target_folder)


def get_image_manager(
    directory_manager: DirectoryManagerDep,
    local_storage: LocalImageStorageDep,
    image_CRUD: ImageCRUDServiceDep,
    metadata_extractor: ImageMetadataExtractorDep,
) -> ImageManager:
    return ImageManager(
        directory_manager=directory_manager,
        local_storage=local_storage,
        image_CRUD=image_CRUD,
        metadata_extractor=metadata_extractor,
    )
