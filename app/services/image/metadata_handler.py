from typing import Dict, Tuple, Any
from pathlib import Path
from fastapi import HTTPException, status
from PIL import Image

import os

from app.core.logging_config import get_logger

logger = get_logger("metadata_handler")


class ImageMetadataExtractor:
    @staticmethod
    def get_dimensions(image_path: Path) -> Tuple[int, int]:
        try:
            with Image.open(image_path) as img:
                return img.width, img.height
        except Exception as e:
            logger.error(f"Error getting image dimensions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get image dimensions: {str(e)}",
            )

    @staticmethod
    def get_metadata(image_path: Path) -> Dict[str, Any]:
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
                    "url": None,
                }
        except FileNotFoundError:
            logger.error(f"Image not found: {image_path}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get image info: {str(e)}",
            )
