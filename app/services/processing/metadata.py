from typing import Dict, Tuple
from pathlib import Path
import os
import logging
from fastapi import HTTPException
from PIL import Image

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Metadata Services")


class ImageMetadata:
    """
    Responsible for retrieving and processing image metadata.
    """
    
    @staticmethod
    def get_dimensions(image_path: Path) -> tuple[int, int]:
        """
        Get the dimensions (width, height) of an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (width, height) in pixels
            
        Raises:
            HTTPException: If dimensions cannot be retrieved
        """
        try:
            with Image.open(image_path) as img:
                return img.width, img.height
        except Exception as e:
            logger.error(f"Error getting image dimensions: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get image dimensions: {str(e)}"
            )
    
    @staticmethod
    def get_metadata(image_path: Path) -> Dict:
        """
        Get metadata about an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing image metadata
            
        Raises:
            HTTPException: If metadata cannot be retrieved
        """
        try:
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
            raise HTTPException(status_code=404, detail="Image not found")
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get image info: {str(e)}"
            )