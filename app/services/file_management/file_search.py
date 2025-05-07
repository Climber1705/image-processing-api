from typing import Dict, List, Optional
from pathlib import Path
import logging
from fastapi import HTTPException

from app.services.file_management.directory_handler import DirectoryHandler
from app.services.data_processing.metadata_processor import MetadataProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("file_handler")


class FileSearch:
    """
    Handles querying image information from the file system.
    """
    
    def __init__(self, directory_manager: DirectoryHandler, metadata_service: MetadataProcessor):
        self.directory_manager = directory_manager
        self.metadata_service = metadata_service
    
    def get_image_path(self, image_id: str, folder: str) -> Path:
        """
        Get the path of the image in the specified folder.
        
        Args:
            image_id: ID/filename of the image
            folder: Which folder the image is in ('uploads', 'processed', 'analyzed')
            
        Returns:
            Path to the image
            
        Raises:
            HTTPException: If image is not found
        """
        directory = self.directory_manager.get_directory(folder)
        image_path = directory / image_id
        
        if not image_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Image {image_id} not found in {folder} folder"
            )
        
        return image_path
    
    def get_image_by_id(self, image_id: str, folder: str) -> Dict:
        """
        Get metadata for an image by its ID in a specific folder.
        
        Args:
            image_id: ID/filename of the image
            folder: Which folder the image is in ('uploads', 'processed', 'analyzed')
            
        Returns:
            Dictionary containing image metadata
            
        Raises:
            HTTPException: If image is not found or metadata cannot be retrieved
        """
        image_path = self.get_image_path(image_id, folder)
        return self.metadata_service.get_metadata(image_path)
    
    def list_images(self, folder: str, directories: Dict[str, Path], limit: int = 100, offset: int = 0, 
                    subdirectory: Optional[str] = None) -> List[Dict]:
        """
        List images in the specified folder with pagination support.
        
        Args:
            folder: Which folder to list ('uploads', 'processed', 'analyzed', 'all')
            limit: Maximum number of images to return
            offset: Starting offset for pagination
            subdirectory: Optional subdirectory to search within
            directories: Dictionary of all available directories
            
        Returns:
            List of dictionaries containing image metadata
            
        Raises:
            HTTPException: If folder is invalid
        """
        # Define folder mapping
        folder_map = {
            "uploads": [directories["uploads"]],
            "processed": [directories["processed"]],
            "analyzed": [directories["analyzed"]],
            "all": [directories["uploads"], directories["processed"], directories["analyzed"]]
        }
        
        if folder not in folder_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid folder: {folder}. Valid options are: {list(folder_map.keys())}"
            )
        
        results = []
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        
        for directory in folder_map[folder]:
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue
                
            try:
                # Build search path
                search_path = directory / subdirectory if subdirectory else directory
                
                # Find all image files recursively
                image_files = [
                    f for f in search_path.rglob('*') 
                    if f.suffix.lower() in valid_extensions and f.is_file()
                ]
                
                # Apply pagination
                start_idx = min(offset, len(image_files))
                end_idx = min(start_idx + limit, len(image_files))
                
                # Process each image
                for img_path in image_files[start_idx:end_idx]:
                    try:
                        img_info = self.metadata_service.get_metadata(img_path)
                        img_info["folder"] = directory.name
                        results.append(img_info)
                    except Exception as e:
                        logger.warning(f"Skipping file {img_path}: {str(e)}")
                        
            except Exception as e:
                logger.error(f"Error listing images in {directory}: {str(e)}")
                continue
        
        return results