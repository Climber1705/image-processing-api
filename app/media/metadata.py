import os
from pathlib import Path

from PIL import Image
from fastapi import HTTPException

from app.core.logging_config import get_logger
from app.media.dtos import FileMetadataDTO

logger = get_logger("metadata")


def get_image_dimensions(image_path: Path) -> tuple[int, int]:
    try:
        with Image.open(image_path) as image:
            return image.width, image.height
    except FileNotFoundError:
        logger.error("Image not found: %s", image_path)
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as exc:
        logger.error("Error getting image dimensions: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get image dimensions: {exc}",
        )


def get_image_metadata(image_path: Path) -> FileMetadataDTO:
    try:
        with Image.open(image_path) as image:
            return FileMetadataDTO(
                filename=Path(image_path).name,
                format=image.format or "",
                mode=image.mode,
                width=image.width,
                height=image.height,
                size_bytes=os.path.getsize(image_path),
                path=str(image_path),
                url=None,
            )
    except FileNotFoundError:
        logger.error("Image not found: %s", image_path)
        raise HTTPException(status_code=404, detail="Image not found")
    except Exception as exc:
        logger.error("Error getting image info: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get image info: {exc}",
        )
