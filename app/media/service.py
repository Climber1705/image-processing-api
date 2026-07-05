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
from app.media.filename import get_display_filename
from app.media.errors import (
    ImageConflictError,
    ImageCreationError,
    ImageNotFoundError,
    ImageOperationError,
    ImageSaveError,
    InvalidFolderError,
    InvalidMoveError,
)
from app.media.hash import compute_checksum
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

    def upload_image(
        self,
        file: UploadFile,
        filename: str | None = None,
        format: str = "JPEG",
    ) -> SaveImageResultDTO:
        extension = self.validator.get_extension(self.validator.validate_format(format))
        display_filename = get_display_filename(filename, file.filename, extension)
        logger.info(f"Saving uploaded image as {display_filename}")

        file.file.seek(0)
        content_hash = compute_checksum(file.file)

        existing = self.repository.get_by_content_hash(content_hash, ImageFolder.UPLOADED)
        if existing is not None:
            logger.info("Duplicate image detected", extra={"content_hash": content_hash})
            return SaveImageResultDTO(path=existing.path, image=record_to_dto(existing))

        image_id = self.repository.generate_id()
        file.file.seek(0)
        file_path = self.storage.save(
            file=file.file,
            folder=ImageFolder.UPLOADED,
            storage_id=image_id,
            format=format,
            display_filename=display_filename,
        )

        try:
            image = self.repository.create(
                image_id=image_id,
                path=file_path,
                folder=ImageFolder.UPLOADED,
                display_filename=display_filename,
                content_hash=content_hash,
            )
            return SaveImageResultDTO(path=file_path, image=image)
        except ImageCreationError:
            self.storage.delete(file_path)
            existing = self.repository.get_by_content_hash(content_hash, ImageFolder.UPLOADED)
            if existing is not None:
                logger.info(
                    "Duplicate image detected after create race",
                    extra={"content_hash": content_hash},
                )
                return SaveImageResultDTO(path=existing.path, image=record_to_dto(existing))
            raise ImageSaveError("Failed to save image") from None
        except Exception as e:
            self.storage.delete(file_path)
            if isinstance(e, (ImageNotFoundError, ImageSaveError)):
                raise
            logger.error(f"Failed to save uploaded image: {e}")
            raise ImageSaveError(f"Failed to save image: {e}") from e

    def get_image_path(
        self,
        filename: str,
        folder: str = ImageFolder.UPLOADED,
    ) -> Path:
        record = self.repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        path = Path(record.path)
        if not self.storage.exists(path):
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        return path

    def get_image_by_id(
        self,
        filename: str,
        folder: str = ImageFolder.UPLOADED,
    ) -> ImageDTO:
        logger.debug(f"Getting image by ID: {filename}")
        record = self.repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        return record_to_dto(record)

    def get_images(
        self,
        folder: str = ImageFolder.UPLOADED,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageDTO]:
        logger.debug(f"Listing images in folder: {folder}, limit={limit}, offset={offset}")
        records = self.repository.list_by_folder(
            folders=ImageFolder.get_folder_names(folder),
            limit=limit,
            offset=offset,
        )
        return [record_to_dto(record) for record in records]

    def delete_image(
        self,
        filename: str,
        folder: str = ImageFolder.UPLOADED,
    ) -> DeleteImageResultDTO:
        logger.info(f"Deleting image with filename: {filename} from folder: {folder}")
        record = self.repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        image = record_to_dto(record)

        if not self.storage.delete(record.path):
            logger.warning(f"File missing for {filename} at {record.path}, removing DB record")
            self.repository.delete_by_filename(filename, folder)
            raise ImageNotFoundError(f"Image {filename} not found in {folder} folder")

        self.repository.delete_by_filename(filename, folder)
        logger.info(f"Deleted image {filename} from {folder}")
        return DeleteImageResultDTO(
            status="success",
            message=f"Image {filename} deleted from {folder}",
            deleted_image=image,
        )

    def delete_images(self, folder: str) -> OperationStatusDTO:
        logger.warning(f"Deleting all images in folder: {folder}")
        if folder not in FolderFilter.values():
            logger.warning(f"Invalid folder: {folder}")
            raise InvalidFolderError(f"Invalid folder: {folder}")

        records = self.repository.list_all_by_folders(ImageFolder.get_folder_names(folder))
        deleted_count = 0

        for record in records:
            try:
                if self.storage.delete(record.path):
                    deleted_count += 1
                elif not self.storage.exists(record.path):
                    deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {record.path}: {e}")

        self.repository.delete_by_folders(ImageFolder.get_folder_names(folder))
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

        record = self.repository.get_by_filename(filename, source_folder)
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
            updated = self.repository.update_location(
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
