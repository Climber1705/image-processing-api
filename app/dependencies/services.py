from fastapi import Request, Depends
from pathlib import Path

from app.core.dependencies import get_directories
from app.dependencies.utils import get_directory_manager, get_file_path_resolver
from app.dependencies.database import get_image_repository
from app.dependencies.storage import get_local_image_storage
from app.media.repository import ImageRepository
from app.editing.image_editor import ImageEditService
from app.media.metadata import ImageMetadataExtractor
from app.media.service import ImageService
from app.vision.detection_service import ObjectDetectionService
from app.vision.inference.engine import InferenceEngine
from app.storage.local_storage import LocalImageStorage
from app.media.utils.directory_utils import DirectoryManager
from app.media.utils.file_utils import FilePathResolver


def get_image_metadata_extractor() -> ImageMetadataExtractor:
    return ImageMetadataExtractor()


def get_image_service(
    local_storage: LocalImageStorage = Depends(get_local_image_storage),
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    metadata_extractor: ImageMetadataExtractor = Depends(get_image_metadata_extractor),
    file_resolver: FilePathResolver = Depends(get_file_path_resolver),
    directories: dict[str, Path] = Depends(get_directories),
    image_repository: ImageRepository = Depends(get_image_repository),
) -> ImageService:
    return ImageService(
        local_storage=local_storage,
        directory_manager=directory_manager,
        metadata_extractor=metadata_extractor,
        file_resolver=file_resolver,
        directories=directories,
        image_repository=image_repository,
    )


def get_object_detection_service(
    request: Request,
    local_storage: LocalImageStorage = Depends(get_local_image_storage),
    image_service: ImageService = Depends(get_image_service),
) -> ObjectDetectionService:
    inference_engine: InferenceEngine | None = getattr(request.app.state, "inference_engine", None)
    if inference_engine is None:
        raise RuntimeError("Inference engine is not initialized")

    return ObjectDetectionService(
        inference_engine=inference_engine,
        local_storage=local_storage,
        image_service=image_service,
    )


def get_image_edit_service(
    image_service: ImageService = Depends(get_image_service),
    local_storage: LocalImageStorage = Depends(get_local_image_storage),
) -> ImageEditService:
    return ImageEditService(
        image_service=image_service,
        local_storage=local_storage,
    )
