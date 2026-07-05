from typing import Any
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.storage.local_storage import LocalImageStorage
from app.media.crud_operations import ImageCRUDService
from app.media.metadata_handler import ImageMetadataExtractor
from app.core.logging_config import get_logger

logger = get_logger("image_service")


class ImageService:
    def __init__(
        self,
        local_storage: LocalImageStorage,
        image_crud: ImageCRUDService,
        metadata_extractor: ImageMetadataExtractor,
    ) -> None:
        self.local_storage = local_storage
        self.image_crud = image_crud
        self.metadata_extractor = metadata_extractor

    def save_uploaded_image(
        self, file: UploadFile, filename: str | None = None, format: str = "JPEG"
    ) -> str:
        try:
            logger.info(f"Saving uploaded image: {filename or file.filename}")
            file.file.seek(0)
            return self.local_storage.save(
                file=file.file, folder="uploaded", filename=filename, format=format
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save uploaded image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    def get_image_path(self, image_name: str, folder: str = "uploaded") -> str:
        logger.debug(f"Getting image path for: {image_name} in folder: {folder}")
        return str(self.image_crud.get_image_path(image_name, folder))

    def get_image_dimensions(self, image_path: Path) -> tuple[int, int]:
        logger.debug(f"Getting image dimensions for: {image_path}")
        return self.metadata_extractor.get_dimensions(image_path)

    def get_image_metadata(self, image_path: Path) -> dict[str, Any]:
        logger.debug(f"Getting metadata for image: {image_path}")
        return self.metadata_extractor.get_metadata(image_path)

    def get_image_by_id(self, image_id: str, folder: str = "uploaded") -> dict[str, Any]:
        logger.debug(f"Getting image by ID: {image_id}")
        return self.image_crud.get_image_by_id(image_id, folder)

    def list_images(
        self,
        folder: str = "uploaded",
        limit: int = 100,
        offset: int = 0,
        subdirectory: str | None = None,
    ) -> list[dict[str, Any]]:
        logger.debug(f"Listing images in folder: {folder}, subdirectory: {subdirectory}")
        return self.image_crud.list_images(folder, limit, offset, subdirectory)

    def delete_image(self, image_id: str, folder: str = "uploaded") -> dict[str, Any]:
        logger.info(f"Deleting image with ID: {image_id} from folder: {folder}")
        return self.image_crud.delete_image(image_id, folder)

    def delete_all_images(self, folder: str) -> dict[str, str]:
        logger.warning(f"Deleting all images in folder: {folder}")
        return self.image_crud.delete_all_images(folder)

    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> dict[str, Any]:
        logger.info(f"Moving image {image_id} from {source_folder} to {target_folder}")
        return self.image_crud.move_image(image_id, source_folder, target_folder)
