import os
from pathlib import Path

from PIL import Image

from app.media.domain.dtos import FileMetadataDTO
from app.media.domain.errors import ImageNotFoundError, ImageOperationError


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
        raise ImageNotFoundError("Image not found")
    except Exception as exc:
        raise ImageOperationError(f"Failed to get image info: {exc}") from exc
