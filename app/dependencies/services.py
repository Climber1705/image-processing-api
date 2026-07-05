from fastapi import Request, Depends
from pathlib import Path

from app.core.dependencies import get_directories
from app.dependencies.utils import get_directory_manager, get_file_path_resolver
from app.dependencies.storage import get_local_image_storage
from app.services.image.image_editor import ImageEditService
from app.services.image.metadata_handler import ImageMetadataExtractor
from app.services.image.crud_operations import ImageCRUDService
from app.services.image.image_service import ImageService
from app.services.detection.detection_service import ObjectDetectionService
from app.services.inference.engine import InferenceEngine
from app.storage.local_storage import LocalImageStorage
from app.utils.file_operations.directory_utils import DirectoryManager
from app.utils.file_operations.file_utils import FilePathResolver

def get_image_metadata_extractor() -> ImageMetadataExtractor:
    return ImageMetadataExtractor()


def get_image_crud_service(
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    metadata_extractor: ImageMetadataExtractor = Depends(get_image_metadata_extractor),
    file_resolver: FilePathResolver = Depends(get_file_path_resolver),
    directories: dict[str, Path] = Depends(get_directories),
) -> ImageCRUDService:
    return ImageCRUDService(
        directory_manager=directory_manager,
        metadata_extractor=metadata_extractor,
        file_resolver=file_resolver,
        directories=directories,
    )

def get_object_detection_service(
    request: Request,
    local_storage: LocalImageStorage = Depends(get_local_image_storage),
) -> ObjectDetectionService:
    inference_engine: InferenceEngine | None = getattr(request.app.state, "inference_engine", None)
    if inference_engine is None:
        raise RuntimeError("Inference engine is not initialized")

    return ObjectDetectionService(
        inference_engine=inference_engine,
        local_storage=local_storage,
    )

def get_image_edit_service(
    image_crud: ImageCRUDService = Depends(get_image_crud_service),
    directories: dict[str, Path] = Depends(get_directories),
) -> ImageEditService:
    return ImageEditService(
        image_crud=image_crud,
        directories=directories,
    )


def get_image_service(
    local_storage: LocalImageStorage = Depends(get_local_image_storage),
    image_crud: ImageCRUDService = Depends(get_image_crud_service),
    metadata_extractor: ImageMetadataExtractor = Depends(get_image_metadata_extractor),
) -> ImageService:
    return ImageService(
        local_storage=local_storage,
        image_crud=image_crud,
        metadata_extractor=metadata_extractor,
    )