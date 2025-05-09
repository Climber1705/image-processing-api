from typing import Dict, List, Optional, Annotated
from pathlib import Path
import shutil


from fastapi import HTTPException, Depends

from app.core.dependencies import get_directories
from app.utils.file_operations.directory_utils import DirectoryManager, get_directory_manager
from app.utils.file_operations.file_utils import FilePathResolver, get_file_path_resolver
from app.services.image.metadata_handler import ImageMetadataExtractor, get_image_metadata_extractor
from app.core.logging_config import get_logger
from app.schemas.image.image_responses import ImageListItem

# Dependency types
DirectoryManagerDep = Annotated[DirectoryManager, Depends(get_directory_manager)]
ImageMetadataExtractorDep = Annotated[ImageMetadataExtractor, Depends(get_image_metadata_extractor)]
FilePathResolverDep = Annotated[FilePathResolver, Depends(get_file_path_resolver)]
DirectoriesDep = Annotated[Dict[str, Path], Depends(get_directories)]


logger = get_logger("crud_operations")

class ImageCRUDService:
    def __init__(
        self,
        directory_manager: DirectoryManagerDep,
        metadata_extractor: ImageMetadataExtractorDep,
        file_resolver: FilePathResolverDep,
        directories: DirectoriesDep
    ):
        """
        Initialize the ImageCRUDService with required dependencies.

        @param directory_manager: Handles directory-related operations.
        @param metadata_extractor: Extracts metadata from images.
        @param file_resolver: Helps to find files in the storage.
        @param directories: Directory mappings for different image categories.

        @returns: None
        """
        self.directory_manager = directory_manager
        self.metadata_extractor = metadata_extractor
        self.file_resolver = file_resolver
        self.directories = directories

    def _get_folder_map(self) -> Dict[str, List[Path]]:
        """
        Get the folder map that associates folder names with directories.

        @returns: A dictionary of folder names and corresponding directory paths.
        """
        return {
            "uploaded": [self.directories["uploaded"]],
            "edited": [self.directories["edited"]],
            "detected": [self.directories["detected"]],
            "all": list(self.directories.values())
        }

    def delete_image(self, image_id: str, folder: str) -> Dict:
        """
        Delete an image and its metadata from the specified folder.

        @param image_id: The ID of the image to delete.
        @param folder: The folder where the image is located.

        @returns: A dictionary with status and message about the deletion.
        """
        directory = self.directory_manager.get_directory(folder)
        image_path = directory / image_id

        if not image_path.exists():
            logger.warning(f"Image {image_id} not found in {folder} folder")
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder} folder")

        try:
            # Extract metadata and delete it if it exists
            image_info = self.metadata_extractor.get_metadata(image_path)
            metadata_path = image_path.with_suffix('.json')
            if metadata_path.exists():
                metadata_path.unlink()
                logger.info(f"Deleted metadata for {image_id}")

            # Delete the image file
            image_path.unlink()
            logger.info(f"Deleted image {image_id} from {folder}")

            return {
                "status": "success",
                "message": f"Image {image_id} deleted from {folder}",
                "deleted_image": image_info
            }
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete image: {e}")

    def delete_all_images(self, folder: str) -> Dict:
        """
        Delete all images from a specified folder.

        @param folder: The folder to delete all images from.

        @returns: A dictionary with status and message about the deletion.
        """
        folder_map = self._get_folder_map()

        if folder not in folder_map:
            logger.warning(f"Invalid folder: {folder}")
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}")

        deleted_count = 0
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

        for directory in folder_map[folder]:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            try:
                image_files = [
                    f for f in directory.rglob('*')
                    if f.suffix.lower() in valid_extensions and f.is_file()
                ]

                for img_path in image_files:
                    try:
                        metadata_path = img_path.with_suffix('.json')
                        if metadata_path.exists():
                            metadata_path.unlink()
                        img_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {img_path}: {e}") 
            except Exception as e:
                logger.error(f"Error cleaning directory {directory}: {e}") 

        logger.info(f"Deleted {deleted_count} images from {folder}") 
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} images from {folder}"
        }

    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> Dict:
        """
        Move an image from one folder to another.

        @param image_id: The ID of the image to move.
        @param source_folder: The folder where the image is currently located.
        @param target_folder: The folder to move the image to.

        @returns: A dictionary with the metadata of the moved image.
        """
        if source_folder == target_folder:
            logger.warning("Source and target folders cannot be the same")
            raise HTTPException(status_code=400, detail="Source and target folders cannot be the same")

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

            # Move metadata if it exists
            source_metadata = source_path.with_suffix('.json')
            if source_metadata.exists():
                target_metadata = target_path.with_suffix('.json')
                shutil.move(str(source_metadata), str(target_metadata))

            logger.info(f"Moved image {image_id} from {source_folder} to {target_folder}")
            return self.metadata_extractor.get_metadata(target_path)

        except Exception as e:
            logger.error(f"Error moving image: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to move image: {e}")

    def get_image_path(self, image_id: str, folder: str) -> Path:
        """
        Get the file path of an image by its ID in a specific folder.

        @param image_id: The ID of the image.
        @param folder: The folder where the image is located.

        @returns: The file path of the image.
        """
        directory = self.directory_manager.get_directory(folder)
        image_path = directory / image_id

        if not image_path.exists():
            logger.warning(f"Image {image_id} not found in {folder}")
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found in {folder}")

        return image_path

    def get_image_by_id(self, image_id: str, folder: str) -> Dict:
        """
        Get the metadata of an image by its ID in a specific folder.

        @param image_id: The ID of the image.
        @param folder: The folder where the image is located.

        @returns: A dictionary with the image's metadata.
        """
        image_path = self.get_image_path(image_id, folder)
        return self.metadata_extractor.get_metadata(image_path)

    def list_images(
        self,
        folder: str,
        limit: int = 100,
        offset: int = 0,
        subdirectory: Optional[str] = None
    ) -> List[Dict]:
        """
        List images from a specific folder.

        @param folder: The folder to list images from.
        @param limit: The maximum number of images to return.
        @param offset: The number of images to skip (for pagination).
        @param subdirectory: Optional subdirectory to search within.

        @returns: A list of image metadata dictionaries.
        """
        folder_map = self._get_folder_map()

        if folder not in folder_map:
            logger.warning(f"Invalid folder: {folder}")
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}. Valid options: {list(folder_map.keys())}")

        results = []
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

        for directory in folder_map[folder]:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue

            try:
                search_path = directory / subdirectory if subdirectory else directory

                image_files = [
                    f for f in search_path.rglob('*')
                    if f.suffix.lower() in valid_extensions and f.is_file()
                ]

                for img_path in image_files[offset:offset + limit]:
                    try:
                        img_info = self.metadata_extractor.get_metadata(img_path)
                        img_info["folder"] = directory.name
                        results.append(ImageListItem(**img_info))
                    except Exception as e:
                        logger.warning(f"Skipping file {img_path}: {e}")
            except Exception as e:
                logger.error(f"Error listing images in {directory}: {e}")

        return results


# Dependency override
def get_image_crud_service(
    directory_manager: DirectoryManagerDep,
    metadata_extractor: ImageMetadataExtractorDep,
    file_resolver: FilePathResolverDep,
    directories: DirectoriesDep
) -> ImageCRUDService:
    """
    Dependency function to get an instance of ImageCRUDService.

    @param directory_manager: Handles directory-related operations.
    @param metadata_extractor: Extracts metadata from images.
    @param file_resolver: Helps to find files in storage.
    @param directories: Directory mappings for different image categories.

    @returns: An instance of ImageCRUDService.
    """
    return ImageCRUDService(
        directory_manager=directory_manager,
        metadata_extractor=metadata_extractor,
        file_resolver=file_resolver,
        directories=directories
    )
