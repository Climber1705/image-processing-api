from fastapi import Depends

from app.core.config import Settings, get_settings
from app.dependencies.validation import get_simple_image_validator
from app.storage.local_storage import LocalImageStorage
from app.validation.simple_validator import SimpleImageValidator


def get_local_image_storage(
    settings: Settings = Depends(get_settings),
    image_validator: SimpleImageValidator = Depends(get_simple_image_validator),
) -> LocalImageStorage:
    return LocalImageStorage(
        directories=settings.directories,
        format_helper=image_validator,
    )
