import shutil
import uuid
from typing import Any
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.media.repository import ImageRepository
from app.media.utils.directory_utils import DirectoryManager
from app.media.utils.file_utils import FilePathResolver
from app.media.schema import ImageListItem
from app.storage.local_storage import LocalImageStorage
from app.core.logging_config import get_logger

logger = get_logger("image_service")


class ImageService:
    def __init__(
        self,
        local_storage: LocalImageStorage,
        directory_manager: DirectoryManager,
        file_resolver: FilePathResolver,
        directories: dict[str, Path],
        image_repository: ImageRepository,
    ) -> None:
        self.local_storage = local_storage
        self.directory_manager = directory_manager
        self.file_resolver = file_resolver
        self.directories = directories
        self.image_repository = image_repository

    def _get_folder_names(self, folder: str) -> list[str]:
        if folder == "all":
            return ["uploaded", "edited", "detected"]
        return [folder]

    def _record_to_list_item(self, record) -> ImageListItem:
        return ImageListItem(**{
            key: value
            for key, value in self.image_repository.to_metadata(record).items()
            if key in ImageListItem.model_fields
        })

    def _get_record_or_404(self, filename: str, folder: str):
        record = self.image_repository.get_by_filename(filename, folder)
        if record is None:
            logger.warning(f"Image {filename} not found in {folder}")
            raise HTTPException(status_code=404, detail=f"Image {filename} not found in {folder}")
        return record

    def _resolve_display_filename(
        self,
        filename: str | None,
        original_filename: str | None,
        format: str,
    ) -> str:
        ext = self.local_storage.image_verifier.get_extension(
            self.local_storage.image_verifier.validate_format(format)
        )
        if filename:
            return f"{Path(filename).stem}{ext}"
        if original_filename:
            original = Path(original_filename)
            return f"{original.stem}{ext}"
        return f"image{ext}"

    def get_or_create_storage_id(self, display_filename: str, folder: str) -> str:
        existing = self.image_repository.get_by_filename(display_filename, folder)
        if existing is not None:
            return existing.id
        return str(uuid.uuid4())

    def register_saved_image(
        self,
        path: str | Path,
        folder: str,
        display_filename: str,
        image_id: str,
    ) -> dict[str, Any]:
        record = self.image_repository.create_record(path, folder, display_filename, image_id)
        return self.image_repository.to_metadata(record)

    def save_uploaded_image(
        self, file: UploadFile, filename: str | None = None, format: str = "JPEG"
    ) -> tuple[str, dict[str, Any]]:
        try:
            display_filename = self._resolve_display_filename(filename, file.filename, format)
            logger.info(f"Saving uploaded image as {display_filename}")
            storage_id = self.get_or_create_storage_id(display_filename, "uploaded")
            file.file.seek(0)
            file_path = self.local_storage.save(
                file=file.file,
                folder="uploaded",
                storage_id=storage_id,
                format=format,
            )
            metadata = self.register_saved_image(
                path=file_path,
                folder="uploaded",
                display_filename=display_filename,
                image_id=storage_id,
            )
            return file_path, metadata
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save uploaded image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save image: {e}")

    def get_image_path(self, image_name: str, folder: str = "uploaded") -> Path:
        record = self._get_record_or_404(image_name, folder)
        path = Path(record.path)
        if not path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_name} not found in {folder}")
        return path

    def get_image_dimensions(self, image_name: str, folder: str = "uploaded") -> tuple[int, int]:
        logger.debug(f"Getting image dimensions for: {image_name} in folder: {folder}")
        record = self._get_record_or_404(image_name, folder)
        return record.width, record.height

    def get_image_by_id(self, image_id: str, folder: str = "uploaded") -> dict[str, Any]:
        logger.debug(f"Getting image by ID: {image_id}")
        record = self._get_record_or_404(image_id, folder)
        return self.image_repository.to_metadata(record)

    def list_images(
        self,
        folder: str = "uploaded",
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageListItem]:
        logger.debug(f"Listing images in folder: {folder}, limit={limit}, offset={offset}")
        records = self.image_repository.list_by_folder(
            folders=self._get_folder_names(folder),
            limit=limit,
            offset=offset,
        )
        return [self._record_to_list_item(record) for record in records]

    def delete_image(self, image_id: str, folder: str = "uploaded") -> dict[str, Any]:
        logger.info(f"Deleting image with ID: {image_id} from folder: {folder}")
        record = self._get_record_or_404(image_id, folder)
        image_path = Path(record.path)
        image_info = self.image_repository.to_metadata(record)

        if not image_path.exists():
            logger.warning(f"File missing for {image_id} at {image_path}, removing DB record")
            self.image_repository.delete_by_filename(image_id, folder)
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder} folder")

        try:
            image_path.unlink()
            self.image_repository.delete_by_filename(image_id, folder)
            logger.info(f"Deleted image {image_id} from {folder}")
            return {
                "status": "success",
                "message": f"Image {image_id} deleted from {folder}",
                "deleted_image": image_info,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete image: {e}")

    def delete_all_images(self, folder: str) -> dict[str, str]:
        logger.warning(f"Deleting all images in folder: {folder}")
        if folder not in {"uploaded", "edited", "detected", "all"}:
            logger.warning(f"Invalid folder: {folder}")
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}")

        records = self.image_repository.list_all_by_folders(self._get_folder_names(folder))
        deleted_count = 0

        for record in records:
            image_path = Path(record.path)
            try:
                if image_path.exists():
                    image_path.unlink()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete {image_path}: {e}")

        self.image_repository.delete_by_folders(self._get_folder_names(folder))
        logger.info(f"Deleted {deleted_count} images from {folder}")
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} images from {folder}",
        }

    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> dict[str, Any]:
        logger.info(f"Moving image {image_id} from {source_folder} to {target_folder}")
        if source_folder == target_folder:
            logger.warning("Source and target folders cannot be the same")
            raise HTTPException(status_code=400, detail="Source and target folders cannot be the same")

        record = self._get_record_or_404(image_id, source_folder)
        source_path = Path(record.path)
        target_path = self.directory_manager.get_directory(target_folder) / source_path.name

        if not source_path.exists():
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {source_folder}")

        if target_path.exists():
            logger.warning(f"Image {image_id} already exists in {target_folder}")
            raise HTTPException(status_code=409, detail=f"Image {image_id} already exists in {target_folder}")

        try:
            shutil.move(str(source_path), str(target_path))
            updated = self.image_repository.update_location(
                filename=image_id,
                source_folder=source_folder,
                target_folder=target_folder,
                new_path=str(target_path),
            )
            logger.info(f"Moved image {image_id} from {source_folder} to {target_folder}")
            return self.image_repository.to_metadata(updated)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error moving image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to move image: {e}")
