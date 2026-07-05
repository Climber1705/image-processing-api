import shutil
from typing import Any
from pathlib import Path
from fastapi import HTTPException

from app.db.repository import ImageRepository
from app.media.utils.directory_utils import DirectoryManager
from app.media.utils.file_utils import FilePathResolver
from app.media.metadata_handler import ImageMetadataExtractor
from app.core.logging_config import get_logger
from app.media.schema import ImageListItem


logger = get_logger("crud_operations")


class ImageCRUDService:
    def __init__(
        self,
        directory_manager: DirectoryManager,
        metadata_extractor: ImageMetadataExtractor,
        file_resolver: FilePathResolver,
        directories: dict[str, Path],
        image_repository: ImageRepository | None = None,
    ):
        self.directory_manager = directory_manager
        self.metadata_extractor = metadata_extractor
        self.file_resolver = file_resolver
        self.directories = directories
        self.image_repository = image_repository

    def _get_folder_map(self) -> dict[str, list[Path]]:
        return {
            "uploaded": [self.directories["uploaded"]],
            "edited": [self.directories["edited"]],
            "detected": [self.directories["detected"]],
            "all": list(self.directories.values()),
        }

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

    def register_saved_image(self, path: str | Path, folder: str) -> dict[str, Any]:
        if self.image_repository is None:
            return self.metadata_extractor.get_metadata(Path(path))

        record = self.image_repository.create_from_path(path, folder)
        return self.image_repository.to_metadata(record)

    def delete_image(self, image_id: str, folder: str) -> dict[str, str | dict[str, Any]]:
        if self.image_repository is not None:
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

        return self._delete_image_from_filesystem(image_id, folder)

    def _delete_image_from_filesystem(self, image_id: str, folder: str) -> dict[str, str | dict[str, Any]]:
        directory = self.directory_manager.get_directory(folder)
        image_path = directory / image_id

        if not image_path.exists():
            logger.warning(f"Image {image_id} not found in {folder} folder")
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder} folder")

        try:
            image_info = self.metadata_extractor.get_metadata(image_path)
            image_path.unlink()
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
        folder_map = self._get_folder_map()

        if folder not in folder_map:
            logger.warning(f"Invalid folder: {folder}")
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}")

        if self.image_repository is not None:
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

        return self._delete_all_images_from_filesystem(folder)

    def _delete_all_images_from_filesystem(self, folder: str) -> dict[str, str]:
        folder_map = self._get_folder_map()
        deleted_count = 0
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

        for directory in folder_map[folder]:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            try:
                image_files = [
                    f for f in directory.rglob("*")
                    if f.suffix.lower() in valid_extensions and f.is_file()
                ]

                for img_path in image_files:
                    try:
                        img_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {img_path}: {e}")
            except Exception as e:
                logger.error(f"Error cleaning directory {directory}: {e}")

        logger.info(f"Deleted {deleted_count} images from {folder}")
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} images from {folder}",
        }

    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> dict[str, Any]:
        if source_folder == target_folder:
            logger.warning("Source and target folders cannot be the same")
            raise HTTPException(status_code=400, detail="Source and target folders cannot be the same")

        if self.image_repository is not None:
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

        return self._move_image_on_filesystem(image_id, source_folder, target_folder)

    def _move_image_on_filesystem(self, image_id: str, source_folder: str, target_folder: str) -> dict[str, Any]:
        source_path = self.directory_manager.get_directory(source_folder) / image_id
        target_path = self.directory_manager.get_directory(target_folder) / image_id

        if not source_path.exists():
            logger.warning(f"Image {image_id} not found in {source_folder}")
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {source_folder}")

        if target_path.exists():
            logger.warning(f"Image {image_id} already exists in {target_folder}")
            raise HTTPException(status_code=409, detail=f"Image {image_id} already exists in {target_folder}")

        try:
            shutil.move(str(source_path), str(target_path))
            logger.info(f"Moved image {image_id} from {source_folder} to {target_folder}")
            return self.metadata_extractor.get_metadata(target_path)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error moving image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to move image: {e}")

    def get_image_path(self, image_id: str, folder: str) -> Path:
        if self.image_repository is not None:
            record = self._get_record_or_404(image_id, folder)
            path = Path(record.path)
            if not path.exists():
                raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder}")
            return path

        directory = self.directory_manager.get_directory(folder)
        image_path = directory / image_id

        if not image_path.exists():
            logger.warning(f"Image {image_id} not found in {folder}")
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder}")

        return image_path

    def get_image_by_id(self, image_id: str, folder: str) -> dict[str, Any]:
        if self.image_repository is not None:
            record = self._get_record_or_404(image_id, folder)
            return self.image_repository.to_metadata(record)

        image_path = self.get_image_path(image_id, folder)
        return self.metadata_extractor.get_metadata(image_path)

    def list_images(
        self,
        folder: str,
        limit: int = 100,
        offset: int = 0,
        subdirectory: str | None = None,
    ) -> list[ImageListItem]:
        if subdirectory is not None:
            return self._list_images_from_filesystem(folder, limit, offset, subdirectory)

        if self.image_repository is not None:
            records = self.image_repository.list_by_folder(
                folders=self._get_folder_names(folder),
                limit=limit,
                offset=offset,
            )
            return [self._record_to_list_item(record) for record in records]

        return self._list_images_from_filesystem(folder, limit, offset, subdirectory)

    def _list_images_from_filesystem(
        self,
        folder: str,
        limit: int,
        offset: int,
        subdirectory: str | None,
    ) -> list[ImageListItem]:
        folder_map = self._get_folder_map()

        if folder not in folder_map:
            logger.warning(f"Invalid folder: {folder}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid folder: {folder}. Valid options: {list(folder_map.keys())}",
            )

        results = []
        valid_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}

        for directory in folder_map[folder]:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            try:
                search_path = directory / subdirectory if subdirectory else directory

                image_files = [
                    f for f in search_path.rglob("*")
                    if f.suffix.lower() in valid_extensions and f.is_file()
                ]

                for img_path in image_files[offset : offset + limit]:
                    try:
                        img_info = self.metadata_extractor.get_metadata(img_path)
                        img_info["folder"] = directory.name
                        results.append(ImageListItem(**img_info))
                    except Exception as e:
                        logger.warning(f"Skipping file {img_path}: {e}")
            except Exception as e:
                logger.error(f"Error listing images in {directory}: {e}")

        return results
