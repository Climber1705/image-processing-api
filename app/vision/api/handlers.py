from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.core.logging_config import get_logger
from app.vision.domain.errors import (
    CorruptImageError,
    InferenceError,
    InvalidInputError,
    ModelNotReadyError,
    VisionDomainError,
)

logger = get_logger("vision_handlers")


async def get_vision_error_response(
    _request: Request,
    exc: VisionDomainError,
    status_code: int,
) -> JSONResponse:
    logger.warning(
        "Vision domain error: %s",
        exc.message,
        extra={"status_code": status_code, "error_type": type(exc).__name__},
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


async def invalid_input_handler(request: Request, exc: InvalidInputError) -> JSONResponse:
    return await get_vision_error_response(request, exc, status.HTTP_400_BAD_REQUEST)


async def model_not_ready_handler(request: Request, exc: ModelNotReadyError) -> JSONResponse:
    return await get_vision_error_response(request, exc, status.HTTP_503_SERVICE_UNAVAILABLE)


async def corrupt_image_handler(request: Request, exc: CorruptImageError) -> JSONResponse:
    return await get_vision_error_response(request, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)


async def inference_error_handler(request: Request, exc: InferenceError) -> JSONResponse:
    return await get_vision_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def vision_domain_error_handler(request: Request, exc: VisionDomainError) -> JSONResponse:
    return await get_vision_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_vision_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidInputError, invalid_input_handler)
    app.add_exception_handler(ModelNotReadyError, model_not_ready_handler)
    app.add_exception_handler(CorruptImageError, corrupt_image_handler)
    app.add_exception_handler(InferenceError, inference_error_handler)
    app.add_exception_handler(VisionDomainError, vision_domain_error_handler)
