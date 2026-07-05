import os
from pathlib import Path

from PIL import Image
from fastapi import HTTPException

from app.core.logging_config import get_logger
from app.media.dtos import FileMetadataDTO

logger = get_logger("metadata")


def get_image_metadata(image_path: Path) -> FileMetadataDTO:
    try:
        with Image.open(image_path) as img:
            return FileMetadataDTO(
                filename=Path(image_path).name,
                format=img.format or "",
                mode=img.mode,
                width=img.width,
                height=img.height,
                size_bytes=os.path.getsize(image_path),
                path=str(image_path),
                url=None,
            )
    except FileNotFoundError:
        logger.error(f"Image not found: {image_path}")
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get image info: {str(e)}",
        )
