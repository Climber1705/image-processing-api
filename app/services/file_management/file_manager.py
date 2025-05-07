from typing import Dict, List, Optional
from pathlib import Path
from fastapi import UploadFile, Depends

from app.services.file_management.directory_handler import DirectoryHandler
from app.services.file_management.storage_manager import StorageManager
from app.services.file_management.file_utils import FileUtils
from app.services.file_management.file_search import FileSearch
from app.services.file_management.image_verfication import ImageVerfication

from app.services.data_processing.metadata_processor import MetadataProcessor

class FileManager:
    """
    Main controller class that delegates to specialized services.
    Provides a unified interface for image file management operations.
    """
    
    def __init__(self,
        directory_manager: DirectoryHandler,
        image_validator: ImageVerfication,
        metadata_service: MetadataProcessor,
        storage_service: StorageManager,
        operation_service: FileUtils,
        query_service: FileSearch,
        folders: Dict[str, str]
    ):
        self.folders = folders
        self.image_validator = image_validator
        self.directory_manager = directory_manager
        self.metadata_service = metadata_service
        self.storage_service = storage_service
        self.operation_service = operation_service
        self.query_service = query_service
    
    def save_uploaded_image(self, file: UploadFile, filename: Optional[str] = None, format: str = "JPEG") -> str:
        """
        Save an uploaded image with format support.
        
        Args:
            file: UploadFile object containing the image
            filename: Optional filename (without extension)
            format: Image format (default: 'JPEG')
            
        Returns:
            Path to the saved image
        """
        directory = self.directory_manager.get_directory("uploads")
        return self.storage_service.save_file(
            file=file,
            directory=directory,
            filename=filename,
            format=format,
        )
    
    def get_image_path(self, image_id: str, folder: str = "uploads") -> str:
        """
        Get the path of the image in the specified folder.
        """
        image_path = self.query_service.get_image_path(image_id, folder)
        return str(image_path)
    
    def get_image_dimensions(self, image_path: Path) -> tuple[int, int]:
        """
        Get the dimensions (width, height) of an image.
        """
        return self.metadata_service.get_dimensions(image_path)
    
    def get_image_metadata(self, image_path: Path) -> Dict:
        """
        Get metadata about an image file.
        """
        return self.metadata_service.get_metadata(image_path)
    
    def get_image_by_id(self, image_id: str, folder: str = "uploads") -> Dict:
        """
        Get metadata for an image by its ID in a specific folder.
        """
        return self.query_service.get_image_by_id(image_id, folder)
    
    def list_images(self, folder: str = "uploads", limit: int = 100, offset: int = 0, 
                   subdirectory: Optional[str] = None) -> List[Dict]:
        """
        List images in the specified folder with pagination support.
        """
        return self.query_service.list_images(folder, self.folders, limit, offset, subdirectory)
    
    def delete_image(self, image_id: str, folder: str = "uploads") -> Dict:
        """
        Delete an image from the specified folder.
        """
        return self.operation_service.delete_image(image_id, folder)
    
    def delete_all_images(self, folder: str) -> Dict:
        """
        Delete all images from the specified folder.
        """
        return self.operation_service.delete_all_images(folder, self.folders)
    
    def move_image(self, image_id: str, source_folder: str, target_folder: str) -> Dict:
        """
        Move an image from one folder to another.
        """
        return self.operation_service.move_image(image_id, source_folder, target_folder)
