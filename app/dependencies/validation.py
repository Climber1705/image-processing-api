from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.logging_config import get_logger
from app.validation.simple_validator import SimpleImageValidator

logger = get_logger("utils")


def get_simple_image_validator(
    settings: Settings = Depends(get_settings),
) -> SimpleImageValidator:
    logger.debug("Creating SimpleImageValidator instance with provided format extensions")
    return SimpleImageValidator(format_extensions=settings.format_extensions)
