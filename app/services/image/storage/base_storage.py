from abc import ABC, abstractmethod
from typing import Optional
from fastapi import UploadFile

class BaseImageStorage(ABC):
    """
    Abstract Base Class for image storage operations.
    This class defines the required methods for saving, retrieving, and deleting images.
    Subclasses should implement these methods with their specific storage logic.
    """
    
    @abstractmethod
    def save(self, file: UploadFile, folder: Optional[str] = None, filename: Optional[str] = None, format: Optional[str] = "JPEG") -> str:
        """
        Save an image and return the storage path or URL.
        
        @param file: The image file to be saved.
        @param folder: The optional folder where the image should be stored (default is None).
        @param filename: The optional filename to save the image as (default is None).
        @param format: The format of the image (e.g., "JPEG", "PNG") to save the image as (default is "JPEG").
        
        @returns: The storage path or URL of the saved image.
        """
        pass  # This method should be implemented by subclasses
    
    @abstractmethod
    def get_url(self, filename: str) -> str:
        """
        Return a public URL or path to the stored image.
        
        @param filename: The name of the image file.
        
        @returns: The URL or path to the stored image.
        """
        pass  # This method should be implemented by subclasses
    
    @abstractmethod
    def delete(self, filename: str) -> bool:
        """
        Delete the image and return success status.
        
        @param filename: The name of the image file to be deleted.
        
        @returns: True if deletion is successful, False otherwise.
        """
        pass  # This method should be implemented by subclasses
