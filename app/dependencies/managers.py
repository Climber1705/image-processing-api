from fastapi import Depends

from app.dependencies.services import (
    get_local_image_storage,
    get_image_crud_service,
    get_image_metadata_extractor,
    get_image_edit_service,
    get_object_detection_service,
)
from app.managers.detection_manager import DetectionManager
from app.managers.edit_manager import EditManager
from app.managers.image_manager import ImageManager
from app.services.detection.detection_service import ObjectDetectionService
from app.services.image.image_editor import ImageEditService
from app.services.image.metadata_handler import ImageMetadataExtractor
from app.services.image.crud_operations import ImageCRUDService
from app.storage.local_storage import LocalImageStorage

def get_detection_manager(
    detection_service: ObjectDetectionService = Depends(get_object_detection_service),
) -> DetectionManager:
    return DetectionManager(detection_service=detection_service)

def get_edit_manager(
    edit_service: ImageEditService = Depends(get_image_edit_service),
) -> EditManager:
    return EditManager(edit_service=edit_service)

def get_image_manager(
    local_storage: LocalImageStorage = Depends(get_local_image_storage),
    image_CRUD: ImageCRUDService = Depends(get_image_crud_service),
    metadata_extractor: ImageMetadataExtractor = Depends(get_image_metadata_extractor),
) -> ImageManager:
    return ImageManager(
        local_storage=local_storage,
        image_CRUD=image_CRUD,
        metadata_extractor=metadata_extractor,
    )