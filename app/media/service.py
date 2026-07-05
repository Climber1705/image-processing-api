import uuid
from pathlib import Path
from fastapi import UploadFile

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.media.domain.dtos import (
    DeleteImageResultDTO,
    ImageDTO,
    OperationStatusDTO,
    SaveImageResultDTO,
)
from app.media.domain.enums import FolderFilter, ImageFolder
from app.media.domain.errors import (
    ImageConflictError,
    ImageCreationError,
    ImageNotFoundError,
    ImageOperationError,
    ImageSaveError,
    InvalidFolderError,
    InvalidMoveError,
)
from app.media.utils.filename import get_display_filename
from app.media.utils.hash import compute_checksum
from app.media.utils.mappers import record_to_dto
from app.media.repository import ImageRepository
from app.storage.base_storage import BaseImageStorage
from app.validation.validator import get_format_extension, validate_image_format

logger = get_logger("image_service")


class ImageService:
    def __init__(
        self,
        settings: Settings,
        repository: ImageRepository,
        storage: BaseImageStorage,
    ) -> None:
        self.repository = repository
        self.storage = storage
        self.settings = settings

    def upload_image(
        self,
        file: UploadFile,
        filename: str | None = None,
        output_format: str = "JPEG",
    ) -> SaveImageResultDTO:
        validated_format = validate_image_format(output_format, self.settings.format_extensions)
        extension = get_format_extension(validated_format, self.settings.format_extensions)
        display_filename = get_display_filename(filename, file.filename, extension)

        file.file.seek(0)
        content_hash = compute_checksum(file.file)

        existing_record = self.repository.get_by_content_hash(content_hash, ImageFolder.UPLOADED)
        if existing_record is not None:
            logger.info("Duplicate image detected", extra={"content_hash": content_hash})
            existing_image = record_to_dto(existing_record)
            return SaveImageResultDTO(path=existing_image.path, image=existing_image)

        image_id = str(uuid.uuid4())
        file.file.seek(0)
        saved_path = self.storage.save(
            file=file.file,
            folder=ImageFolder.UPLOADED,
            storage_id=image_id,
            format=output_format,
            display_filename=display_filename,
        )

        try:
            image = self.repository.create(
                image_id=image_id,
                path=saved_path,
                folder=ImageFolder.UPLOADED,
                display_filename=display_filename,
                content_hash=content_hash,
            )
            return SaveImageResultDTO(
                path=saved_path,
                image=image,
            )
        except ImageCreationError:
            self.storage.delete(saved_path)
            existing_record = self.repository.get_by_content_hash(content_hash, ImageFolder.UPLOADED)
            if existing_record is not None:
                logger.info(
                    "Duplicate image detected after create race",
                    extra={"content_hash": content_hash},
                )
                existing_image = record_to_dto(existing_record)
                return SaveImageResultDTO(
                    path=existing_image.path,
                    image=existing_image,
                )
            raise ImageSaveError("Failed to save image") from None
        except Exception as exc:
            self.storage.delete(saved_path)
            if isinstance(exc, (ImageNotFoundError, ImageSaveError)):
                raise
            logger.error("Failed to save uploaded image: %s", exc)
            raise ImageSaveError(f"Failed to save image: {exc}") from exc

    def get_image_path(self, filename: str, folder: str = ImageFolder.UPLOADED) -> Path:
        record = self.repository.get_by_filename(filename, folder)
        if record is None:
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")

        path = Path(record.path)
        if not self.storage.exists(path):
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        return path

    def get_image_by_filename(
        self,
        filename: str,
        folder: str = ImageFolder.UPLOADED,
    ) -> ImageDTO:
        record = self.repository.get_by_filename(filename, folder)
        if record is None:
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")
        return record_to_dto(record)

    def get_images(
        self,
        folder: str = ImageFolder.UPLOADED,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageDTO]:
        records = self.repository.get_by_folder(
            folders=ImageFolder.get_folder_names(folder),
            limit=limit,
            offset=offset,
        )
        return [record_to_dto(record) for record in records]

    def delete_image(self, filename: str, folder: str = ImageFolder.UPLOADED) -> DeleteImageResultDTO:
        record = self.repository.get_by_filename(filename, folder)
        if record is None:
            raise ImageNotFoundError(f"Image {filename} not found in {folder}")

        deleted_image = record_to_dto(record)
        if not self.storage.delete(record.path):
            logger.warning(
                "File missing for %s at %s, removing DB record",
                filename,
                record.path,
            )
            self.repository.delete_by_filename(filename, folder)
            raise ImageNotFoundError(f"Image {filename} not found in {folder} folder")

        self.repository.delete_by_filename(filename, folder)
        return DeleteImageResultDTO(
            status="success",
            message=f"Image {filename} deleted from {folder}",
            deleted_image=deleted_image,
        )

    def delete_images(self, folder: str) -> OperationStatusDTO:
        logger.warning("Deleting all images in folder: %s", folder)
        if folder not in FolderFilter.values():
            raise InvalidFolderError(f"Invalid folder: {folder}")

        records = self.repository.get_all_by_folders(ImageFolder.get_folder_names(folder))
        deleted_count = 0

        for record in records:
            try:
                if self.storage.delete(record.path):
                    deleted_count += 1
                elif not self.storage.exists(record.path):
                    deleted_count += 1
            except Exception as exc:
                logger.warning("Failed to delete %s: %s", record.path, exc)

        self.repository.delete_by_folders(ImageFolder.get_folder_names(folder))
        return OperationStatusDTO(
            status="success",
            message=f"Deleted {deleted_count} images from {folder}",
        )

    def move_image(self, filename: str, source_folder: str, target_folder: str) -> ImageDTO:
        if source_folder == target_folder:
            raise InvalidMoveError("Source and target folders cannot be the same")

        record = self.repository.get_by_filename(filename, source_folder)
        if record is None:
            raise ImageNotFoundError(f"Image {filename} not found in {source_folder}")

        if not self.storage.exists(record.path):
            raise ImageNotFoundError(f"Image {filename} not found in {source_folder}")

        destination_path = self.storage.destination_path(record.path, target_folder)
        if self.storage.exists(destination_path):
            raise ImageConflictError(f"Image {filename} already exists in {target_folder}")

        try:
            new_path = self.storage.move(record.path, target_folder)
            updated_image = self.repository.update(
                filename=filename,
                source_folder=source_folder,
                target_folder=target_folder,
                new_path=new_path,
            )
            if updated_image is None:
                raise ImageOperationError("Failed to update image location")
            return updated_image
        except (ImageNotFoundError, ImageConflictError, InvalidMoveError, ImageOperationError):
            raise
        except Exception as exc:
            logger.error("Error moving image: %s", exc)
            raise ImageOperationError(f"Failed to move image: {exc}") from exc
