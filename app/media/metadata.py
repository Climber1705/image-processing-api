import os
from typing import Any
from PIL import Image
from pathlib import Path
from fastapi import HTTPException

from app.core.logging_config import get_logger

logger = get_logger("metadata")


def get_image_dimensions(image_path: Path) -> tuple[int, int]:
    try:
        with Image.open(image_path) as img:
            return img.width, img.height
    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get image dimensions: {str(e)}",
        )


def get_image_metadata(image_path: Path) -> dict[str, Any]:
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
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get image info: {str(e)}",
            )
