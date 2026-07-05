from pathlib import Path
from fastapi import Depends

from app.core.dependencies import get_format_extensions, get_directories
from app.core.logging_config import get_logger
from app.media.utils.directory_utils import DirectoryManager
from app.media.utils.validator.simple_validator import SimpleImageValidator
from app.media.utils.file_utils import FilePathResolver

logger = get_logger("utils")

def get_simple_image_validator(
    format_extensions: dict[str, str] = Depends(get_format_extensions),
) -> SimpleImageValidator:
    logger.debug("Creating SimpleImageValidator instance with provided format extensions")
    return SimpleImageValidator(format_extensions=format_extensions)

def get_directory_manager(
    directories: dict[str, Path] = Depends(get_directories),
) -> DirectoryManager:
    logger.debug("Creating DirectoryManager instance with directories: %s", directories)
    return DirectoryManager(directories=directories)

def get_file_path_resolver(
    directories: dict[str, Path] = Depends(get_directories),
) -> FilePathResolver:
    logger.debug("Creating FilePathResolver instance with directories: %s", directories)
    return FilePathResolver(directories=directories)