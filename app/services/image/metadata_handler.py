from typing import Dict, Tuple
from pathlib import Path
from fastapi import HTTPException, status
from PIL import Image

import os

from app.core.logging_config import get_logger

# Initialize the logger
logger = get_logger("metadata_handler")

class ImageMetadataExtractor:
    """
    A class for extracting metadata and dimensions from image files.
    """

    @staticmethod
    def get_dimensions(image_path: Path) -> Tuple[int, int]:
        """
        Get the dimensions (width and height) of an image.

        @param image_path: The path to the image file.
        @returns: A tuple (width, height) representing the image's dimensions.
        @raises HTTPException: If there is an error while getting image dimensions.
        """
        try:
            # Open the image and return its width and height
            with Image.open(image_path) as img:
                return img.width, img.height
        except Exception as e:
            logger.error(f"Error getting image dimensions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get image dimensions: {str(e)}"
            )
    
    @staticmethod
    def get_metadata(image_path: Path) -> Dict:
        """
        Get the metadata of an image, including its filename, format, mode, size, etc.

        @param image_path: The path to the image file.
        @returns: A dictionary containing the image metadata.
        @raises HTTPException: If there is an error while getting image metadata or the image is not found.
        """
        try:
            # Open the image and extract its metadata
            with Image.open(image_path) as img:
                return {
                    "filename": Path(image_path).name,  
                    "format": img.format,               
                    "mode": img.mode,                   
                    "width": img.width,               
                    "height": img.height,             
                    "size_bytes": os.path.getsize(image_path), 
                    "path": str(image_path),           
                    "url": None                     
                }
        except FileNotFoundError:
            logger.error(f"Image not found: {image_path}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get image info: {str(e)}"
            )
    
def get_image_metadata_extractor() -> ImageMetadataExtractor:
    """
    Dependency injection to get an instance of ImageMetadataExtractor.

    @returns: An instance of the ImageMetadataExtractor class.
    """
    return ImageMetadataExtractor()