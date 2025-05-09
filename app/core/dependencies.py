
from typing import Dict
from pathlib import Path
from app.core.config import settings
from app.core.logging_config import get_logger

# Initialize logger for this module
logger = get_logger("dependencies")


def get_directories() -> Dict[str, Path]:
    """
    Retrieve the configured storage directories.

    @return: A dict mapping directory keys to their Path objects:
        - "uploaded": folder for uploaded images
        - "edited": folder for edited images
        - "detected": folder for detection output
    """
    dirs = {
        "uploaded": settings.UPLOADED_FOLDER,
        "edited": settings.EDITED_FOLDER,
        "detected": settings.DETECTED_FOLDER
    }
    logger.debug(f"Configured directories: {dirs}")
    return dirs

def get_format_extensions() -> Dict[str, str]:
    """
    Retrieve the mapping from image format names to file extensions.

    @return: A dict mapping format strings (e.g., "JPEG", "PNG") to their
             corresponding file extension (e.g., ".jpg", ".png").
    """
    fmt_ext = {
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "PNG": ".png",
        "GIF": ".gif",
        "BMP": ".bmp",
        "TIFF": ".tiff",
        "WEBP": ".webp"
    }
    logger.debug(f"Supported format extensions: {fmt_ext}")
    return fmt_ext
