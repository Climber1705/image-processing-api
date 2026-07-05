from fastapi import Depends

from app.dependencies.utils import get_directory_manager, get_simple_image_validator, get_file_path_resolver
from app.storage.local_storage import LocalImageStorage
from app.media.utils.directory_utils import DirectoryManager
from app.media.utils.validator.simple_validator import SimpleImageValidator
from app.media.utils.file_utils import FilePathResolver

def get_local_image_storage(
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    image_validator: SimpleImageValidator = Depends(get_simple_image_validator),
    file_resolver: FilePathResolver = Depends(get_file_path_resolver),
) -> LocalImageStorage:
    return LocalImageStorage(
        directory_manager=directory_manager,
        image_validator=image_validator,
        file_resolver=file_resolver,
    )