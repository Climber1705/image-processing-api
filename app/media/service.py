import uuid
from pathlib import Path
from fastapi import UploadFile

from app.core.logging_config import get_logger
from app.media.dtos import (
    DeleteImageResultDTO,
    ImageDTO,
    OperationStatusDTO,
    SaveImageResultDTO,
)
from app.media.enums import FolderFilter, ImageFolder
from app.media.errors import (
    ImageConflictError,
    ImageNotFoundError,
    ImageOperationError,
    ImageSaveError,
    InvalidFolderError,
    InvalidMoveError,
)
from app.media.mappers import record_to_dto
from app.media.repository import ImageRepository
from app.storage.base_storage import BaseImageStorage
from app.validation.simple_validator import SimpleImageValidator

logger = get_logger("image_service")


class ImageService:
    
    def __init__(
        self,
        repository: ImageRepository,
        storage: BaseImageStorage,
        validator: SimpleImageValidator,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.validator = validator

    def _resolve_display_filename(
        self,
        filename: str | None,
        original_filename: str | None,
        format: str,
    ) -> str:
        ext = self.validator.get_extension(self.validator.validate_format(format))
        if filename:
            return f"{Path(filename).stem}{ext}"
        if original_filename:
            original = Path(original_filename)
            return f"{original.stem}{ext}"
        return f"image{ext}"

    def get_or_create_storage_id(self, display_filename: str, folder: str) -> str:
        existing = self.repository.get_by_filename(display_filename, folder)
        if existing is not None:
            return existing.id
        return str(uuid.uuid4())

    def upload_image(
        self, file: UploadFile, filename: str | None = None, format: str = "JPEG"
    ) -> SaveImageResultDTO:
        try:
            display_filename = self._resolve_display_filename(filename, file.filename, format)
            logger.info(f"Saving uploaded image as {display_filename}")
            storage_id = self.get_or_create_storage_id(display_filename, ImageFolder.UPLOADED)
            file.file.seek(0)
            file_path = self.storage.save(
                file=file.file,
                folder=ImageFolder.UPLOADED,
                storage_id=storage_id,
                format=format,
            )
            image = self.image_repository.create_record(
                path=file_path,
                folder=ImageFolder.UPLOADED,
                display_filename=display_filename,
                image_id=storage_id,
            )
            return SaveImageResultDTO(path=file_path, image=image)
        except Exception as e:
            if isinstance(e, (ImageNotFoundError, ImageSaveError)):
                raise
            logger.error(f"Failed to save uploaded image: {e}")
            raise ImageSaveError(f"Failed to save image: {e}") from e

    def get_image_path(self, filename: str, folder: str = ImageFolder.UPLOADED) -> Path:
        record = self.image_repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        path = Path(record.path)
        if not self.storage.exists(path):
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        return path

    def get_image_by_id(self, filename: str, folder: str = ImageFolder.UPLOADED) -> ImageDTO:
        logger.debug(f"Getting image by ID: {filename}")
        record = self.image_repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        return record_to_dto(record)

    def list_images(
        self,
        folder: str = ImageFolder.UPLOADED,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageDTO]:
        logger.debug(f"Listing images in folder: {folder}, limit={limit}, offset={offset}")
        records = self.image_repository.list_by_folder(
            folders=ImageFolder.get_folder_names(folder),
            limit=limit,
            offset=offset,
        )
        return [record_to_dto(record) for record in records]

    def delete_image(self, filename: str, folder: str = ImageFolder.UPLOADED) -> DeleteImageResultDTO:
        logger.info(f"Deleting image with filename: {filename} from folder: {folder}")
        record = self.image_repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        image = record_to_dto(record)

        if not self.storage.delete(record.path):
            logger.warning(f"File missing for {filename} at {record.path}, removing DB record")
            self.image_repository.delete_by_filename(filename, folder)
            raise ImageNotFoundError(f"Image {filename} not found in {folder} folder")

        self.image_repository.delete_by_filename(filename, folder)
        logger.info(f"Deleted image {filename} from {folder}")
        return DeleteImageResultDTO(
            status="success",
            message=f"Image {filename} deleted from {folder}",
            deleted_image=image,
        )

    def delete_all_images(self, folder: str) -> OperationStatusDTO:
        logger.warning(f"Deleting all images in folder: {folder}")
        if folder not in FolderFilter.values():
            logger.warning(f"Invalid folder: {folder}")
            raise InvalidFolderError(f"Invalid folder: {folder}")

        records = self.image_repository.list_all_by_folders(ImageFolder.get_folder_names(folder))
        deleted_count = 0

        for record in records:
            try:
                if self.storage.delete(record.path):
                    deleted_count += 1
                elif not self.storage.exists(record.path):
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {record.path}: {e}")

        self.image_repository.delete_by_folders(ImageFolder.get_folder_names(folder))
        logger.info(f"Deleted {deleted_count} images from {folder}")
        return OperationStatusDTO(
            status="success",
            message=f"Deleted {deleted_count} images from {folder}",
        )

    def move_image(self, filename: str, source_folder: str, target_folder: str) -> ImageDTO:
        logger.info(f"Moving image {filename} from {source_folder} to {target_folder}")
        if source_folder == target_folder:
            logger.warning("Source and target folders cannot be the same")
            raise InvalidMoveError("Source and target folders cannot be the same")

        record = self.image_repository.get_by_filename(filename, source_folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {source_folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {source_folder}")

        if not self.storage.exists(record.path):
            raise ImageNotFoundError(f"Image {filename} not found in {source_folder}")

        dest_path = self.storage.destination_path(record.path, target_folder)
        if self.storage.exists(dest_path):
            logger.warning(f"Image {filename} already exists in {target_folder}")
            raise ImageConflictError(f"Image {filename} already exists in {target_folder}")

        try:
            new_path = self.storage.move(record.path, target_folder)
            updated = self.image_repository.update_location(
                filename=filename,
                source_folder=source_folder,
                target_folder=target_folder,
                new_path=new_path,
            )
            if updated is None:
                raise ImageOperationError("Failed to update image location")
            logger.info(f"Moved image {filename} from {source_folder} to {target_folder}")
            return record_to_dto(updated)
        except (ImageNotFoundError, ImageConflictError, InvalidMoveError, ImageOperationError):
            raise
        except Exception as e:
            logger.error(f"Error moving image: {e}")
            raise ImageOperationError(f"Failed to move image: {e}") from e
