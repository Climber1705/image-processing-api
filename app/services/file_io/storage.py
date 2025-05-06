from typing import Optional
from pathlib import Path
import os
import uuid
import logging
from fastapi import HTTPException, UploadFile
from PIL import Image

from app.services.file_io.directory_manager import DirectoryManager
from app.services.file_io.image_validator import ImageValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("file_handler")


class ImageStorage:
    """
    Handles file system operations for saving and managing images.
    """
    
    def __init__(self, directory_manager: DirectoryManager, image_validator: ImageValidator):
        self.directory_manager = directory_manager
        self.image_validator = image_validator
    
    def _get_file_name(self, filename: Optional[str], format: str = "JPEG") -> str:
        """
        Generate a filename with proper extension.
        
        Args:
            filename: Optional base filename (without extension)
            format: Image format (default: 'JPEG')
            
        Returns:
            Generated filename with appropriate extension
            
        Raises:
            HTTPException: If format is not supported
        """
        format = self.image_validator.validate_format(format)
        ext = self.image_validator.get_extension(format)
        if filename is None:
            return f"{uuid.uuid4()}{ext}"
        
        if not filename.lower().endswith(ext.lower()):
            return f"{Path(filename).stem}{ext}"
        return filename
    
    def save_file(self, 
                 file: UploadFile, 
                 directory: Path, 
                 filename: Optional[str] = None, 
                 format: str = "JPEG") -> str:
        """
        Save an uploaded file, converting to the specified format if needed.
        
        Args:
            file: UploadFile object containing the image
            directory: Directory path to save the file
            filename: Optional filename (without extension)
            format: Image format (default: 'JPEG')
            
        Returns:
            Path to the saved image
            
        Raises:
            HTTPException: If file cannot be saved
        """
        filename = self._get_file_name(filename, format)
        file_location = directory / filename

        try:
            with Image.open(file.file) as img:
                img.save(file_location, format=format.upper())
                
            logger.info(f"Saved file {filename} to {directory}")
            return str(file_location)
            
        except Image.UnidentifiedImageError:
            if file_location.exists():
                os.remove(file_location)
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a valid image"
            )
        except Exception as e:
            if file_location.exists():
                os.remove(file_location)
            logger.error(f"Error saving file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )