from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.core.logging_config import get_logger
from app.media.domain.errors import (
    DuplicateImageError,
    ImageConflictError,
    ImageCreationError,
    ImageNotFoundError,
    ImageOperationError,
    ImageSaveError,
    InvalidFolderError,
    InvalidMoveError,
    MediaDomainError,
)

logger = get_logger("media_handlers")


async def get_media_error_response(
    _request: Request,
    exc: MediaDomainError,
    status_code: int,
) -> JSONResponse:
    logger.warning(
        "Media domain error: %s",
        exc.message,
        extra={"status_code": status_code, "error_type": type(exc).__name__},
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


async def image_not_found_handler(request: Request, exc: ImageNotFoundError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_404_NOT_FOUND)


async def duplicate_image_handler(request: Request, exc: DuplicateImageError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_409_CONFLICT)


async def invalid_folder_handler(request: Request, exc: InvalidFolderError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_400_BAD_REQUEST)


async def invalid_move_handler(request: Request, exc: InvalidMoveError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_400_BAD_REQUEST)


async def image_conflict_handler(request: Request, exc: ImageConflictError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_409_CONFLICT)


async def image_save_handler(request: Request, exc: ImageSaveError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def image_operation_handler(request: Request, exc: ImageOperationError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def image_creation_handler(request: Request, exc: ImageCreationError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_409_CONFLICT)


async def media_domain_error_handler(request: Request, exc: MediaDomainError) -> JSONResponse:
    return await get_media_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_media_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ImageNotFoundError, image_not_found_handler)
    app.add_exception_handler(DuplicateImageError, duplicate_image_handler)
    app.add_exception_handler(InvalidFolderError, invalid_folder_handler)
    app.add_exception_handler(InvalidMoveError, invalid_move_handler)
    app.add_exception_handler(ImageConflictError, image_conflict_handler)
    app.add_exception_handler(ImageSaveError, image_save_handler)
    app.add_exception_handler(ImageOperationError, image_operation_handler)
    app.add_exception_handler(ImageCreationError, image_creation_handler)
    app.add_exception_handler(MediaDomainError, media_domain_error_handler)
