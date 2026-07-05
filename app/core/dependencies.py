from typing import Dict
from pathlib import Path

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger("dependencies")


def get_directories() -> Dict[str, Path]:
    dirs = {
        "uploaded": settings.UPLOADED_FOLDER,
        "edited": settings.EDITED_FOLDER,
        "detected": settings.DETECTED_FOLDER,
    }
    logger.debug(f"Configured directories: {dirs}")
    return dirs


def get_format_extensions() -> Dict[str, str]:
    fmt_ext = {
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "WEBP": ".webp",
    }
    logger.debug(f"Supported format extensions: {fmt_ext}")
    return fmt_ext
