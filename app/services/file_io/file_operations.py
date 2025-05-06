from typing import Dict
from pathlib import Path
import shutil
import logging
from fastapi import HTTPException

from app.services.file_io.directory_manager import DirectoryManager
from app.services.processing.metadata import ImageMetadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("file_handler")


class ImageOperation:
    """
    Handles operations that modify images (delete, move).
    """
    
    def __init__(self, directory_manager: DirectoryManager, metadata_service: ImageMetadata):
        self.directory_manager = directory_manager
        self.metadata_service = metadata_service
    
    def delete_image(self, image_id: str, folder: str) -> Dict:
        """
        Delete an image from the specified folder.
        
        Args:
            image_id: ID/filename of the image to delete
            folder: Which folder the image is in ('uploads', 'processed', 'analyzed')
            
        Returns:
            dict: Status information
            
        Raises:
            HTTPException: If deletion fails
        """
        directory = self.directory_manager.get_directory(folder)
        image_path = directory / image_id
        
        if not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Image {image_id} not found in {folder} folder"
            )
        
        try:
            # Get image info before deletion
            image_info = self.metadata_service.get_metadata(image_path)
            
            # Check for metadata file
            metadata_path = image_path.with_suffix('.json')
            if metadata_path.exists():
                metadata_path.unlink()
                logger.info(f"Deleted metadata file for {image_id}")
            
            # Delete the image
            image_path.unlink()
            logger.info(f"Deleted image {image_id} from {folder} folder")
            
            return {
                "status": "success",
                "message": f"Image {image_id} deleted from {folder} folder",
                "deleted_image": image_info
            }
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete image: {str(e)}"
            )
    
    def delete_all_images(self, folder: str, directories: Dict[str, Path]) -> Dict:
        """
        Delete all images from the specified folder.
        
        Args:
            folder: Which folder to clear ('uploads', 'processed', 'analyzed', 'all')
            directories: Dictionary of all available directories
            
        Returns:
            dict: Status information
            
        Raises:
            HTTPException: If deletion fails
        """
        folder_map = directories.copy()
        folder_map["all"] = list(directories.values())
        
        if folder not in folder_map:
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}")
        
        deleted_count = 0
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        
        folders_to_process = [folder_map[folder]] if folder != "all" else folder_map[folder]
        
        for directory in folders_to_process:
            if not directory.exists():
                continue
                
            try:
                # Get all image files
                image_files = [
                    f for f in directory.glob('**/*') 
                    if f.suffix.lower() in valid_extensions and f.is_file()
                ]
                
                # Delete all images and their metadata
                for img_path in image_files:
                    try:
                        # Delete metadata if exists
                        metadata_path = img_path.with_suffix('.json')
                        if metadata_path.exists():
                            metadata_path.unlink()
                        
                        # Delete image
                        img_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete {img_path}: {e}")
            except Exception as e:
                logger.error(f"Error while cleaning directory {directory}: {e}")
        
        logger.info(f"Deleted {deleted_count} images from {folder} folder(s)")
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} images from {folder} folder(s)"
        }
    
    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> Dict:
        """
        Move an image from one folder to another.
        
        Args:
            image_id: ID/filename of the image to move
            source_folder: Source folder ('uploads', 'processed', 'analyzed')
            target_folder: Target folder ('uploads', 'processed', 'analyzed')
            
        Returns:
            dict: Updated image information
            
        Raises:
            HTTPException: If move operation fails
        """
        if source_folder == target_folder:
            raise HTTPException(
                status_code=400,
                detail="Source and target folders cannot be the same"
            )
        
        source_path = self.directory_manager.get_directory(source_folder) / image_id
        target_path = self.directory_manager.get_directory(target_folder) / image_id
        
        if not source_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Image {image_id} not found in {source_folder} folder"
            )
            
        if target_path.exists():
            raise HTTPException(
                status_code=409,
                detail=f"Image {image_id} already exists in {target_folder} folder"
            )
        
        try:
            # Move the image
            shutil.move(str(source_path), str(target_path))
            
            # Move metadata if it exists
            source_metadata = source_path.with_suffix('.json')
            if source_metadata.exists():
                target_metadata = target_path.with_suffix('.json')
                shutil.move(str(source_metadata), str(target_metadata))
            
            logger.info(f"Moved image {image_id} from {source_folder} to {target_folder}")
            return self.metadata_service.get_metadata(target_path)
        except Exception as e:
            logger.error(f"Error moving image: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to move image: {str(e)}"
            )