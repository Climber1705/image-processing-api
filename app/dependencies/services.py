from fastapi import Request, Depends

from app.dependencies.validation import get_simple_image_validator
from app.dependencies.repositories import get_image_repository
from app.dependencies.storage import get_local_image_storage
from app.media.repository import ImageRepository
from app.editing.image_editor import ImageEditService
from app.media.service import ImageService
from app.vision.detection_service import ObjectDetectionService
from app.vision.inference.engine import InferenceEngine
from app.storage.base_storage import BaseImageStorage
from app.validation.simple_validator import SimpleImageValidator


def get_image_service(
    image_repository: ImageRepository = Depends(get_image_repository),
    storage: BaseImageStorage = Depends(get_local_image_storage),
    validator: SimpleImageValidator = Depends(get_simple_image_validator),
) -> ImageService:
    return ImageService(
        repository=image_repository,
        storage=storage,
        validator=validator,
    )


def get_object_detection_service(
    request: Request,
    storage: BaseImageStorage = Depends(get_local_image_storage),
    image_service: ImageService = Depends(get_image_service),
    image_repository: ImageRepository = Depends(get_image_repository),
) -> ObjectDetectionService:
    inference_engine: InferenceEngine | None = getattr(request.app.state, "inference_engine", None)
    if inference_engine is None:
        raise RuntimeError("Inference engine is not initialized")

    return ObjectDetectionService(
        inference_engine=inference_engine,
        storage=storage,
        image_service=image_service,
        image_repository=image_repository,
    )


def get_image_edit_service(
    image_service: ImageService = Depends(get_image_service),
    image_repository: ImageRepository = Depends(get_image_repository),
    storage: BaseImageStorage = Depends(get_local_image_storage),
) -> ImageEditService:
    return ImageEditService(
        image_service=image_service,
        image_repository=image_repository,
        storage=storage,
    )
