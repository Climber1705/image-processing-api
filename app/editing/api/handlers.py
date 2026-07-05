from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.core.logging_config import get_logger
from app.editing.domain.errors import (
    EditDomainError,
    ImageEditError,
    InvalidEditParamsError,
)

logger = get_logger("editing_handlers")


async def get_edit_error_response(
    _request: Request,
    exc: EditDomainError,
    status_code: int,
) -> JSONResponse:
    logger.warning(
        "Editing domain error: %s",
        exc.message,
        extra={"status_code": status_code, "error_type": type(exc).__name__},
    )
    return JSONResponse(status_code=status_code, content={"detail": exc.message})


async def invalid_edit_params_handler(
    request: Request,
    exc: InvalidEditParamsError,
) -> JSONResponse:
    return await get_edit_error_response(request, exc, status.HTTP_422_UNPROCESSABLE_ENTITY)


async def image_edit_error_handler(request: Request, exc: ImageEditError) -> JSONResponse:
    return await get_edit_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


async def edit_domain_error_handler(request: Request, exc: EditDomainError) -> JSONResponse:
    return await get_edit_error_response(request, exc, status.HTTP_500_INTERNAL_SERVER_ERROR)


def register_editing_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(InvalidEditParamsError, invalid_edit_params_handler)
    app.add_exception_handler(ImageEditError, image_edit_error_handler)
    app.add_exception_handler(EditDomainError, edit_domain_error_handler)
