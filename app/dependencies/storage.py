from app.core.config import Settings, get_settings
from app.storage.local_storage import LocalImageStorage
from fastapi import Depends


def get_local_image_storage(
    settings: Settings = Depends(get_settings),
) -> LocalImageStorage:
    return LocalImageStorage(
        directories=settings.directories,
        format_extensions=settings.format_extensions,
    )
