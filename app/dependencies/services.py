from app.core.config import Settings, get_settings
from app.dependencies.repositories import get_image_repository
from app.dependencies.storage import get_local_image_storage
from app.editing.service import ImageEditService
from app.media.repository import ImageRepository
from app.media.service import ImageService
from app.storage.base_storage import BaseImageStorage
from app.vision.service import InferenceService
from fastapi import Depends, Request


def get_image_service(
    image_repository: ImageRepository = Depends(get_image_repository),
    storage: BaseImageStorage = Depends(get_local_image_storage),
    settings: Settings = Depends(get_settings),
) -> ImageService:
    return ImageService(
        settings=settings,
        repository=image_repository,
        storage=storage,
    )


def get_inference_service(
    request: Request,
    storage: BaseImageStorage = Depends(get_local_image_storage),
    image_service: ImageService = Depends(get_image_service),
    image_repository: ImageRepository = Depends(get_image_repository),
) -> InferenceService:
    inference_engine = getattr(request.app.state, "inference_engine", None)
    if inference_engine is None:
        raise RuntimeError("Inference engine is not initialized")

    return InferenceService(
        engine=inference_engine,
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
