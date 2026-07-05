from fastapi import APIRouter, Depends, Query, Request
from typing import Annotated
import asyncio

from app.managers.edit_manager import EditManager, get_edit_manager
from app.schemas.editing.editing_requests import RotateEditRequest, SharpenEditRequest
from app.schemas.editing.editing_responses import EditResponse
from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger

logger = get_logger("editing_routes")

router = APIRouter(prefix="/images/edit", tags=["Image Editing"])

EditManagerDep = Annotated[EditManager, Depends(get_edit_manager)]


@router.post("/resize", response_model=EditResponse)
@limiter.limit("10/minute")
async def resize_image(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    width: int = Query(..., gt=0, description="The target width for resizing (must be greater than 0)."),
    height: int = Query(..., gt=0, description="The target height for resizing (must be greater than 0)."),
):
    """Resize an image to the given width and height."""
    path = await asyncio.to_thread(
        service.process_image_edit, image_name, service.apply_resize, image_name, width, height
    )
    return EditResponse(path=path)


@router.post("/grayscale", response_model=EditResponse)
@limiter.limit("20/minute")
async def convert_to_grayscale(
    request: Request,
    image_name: str,
    service: EditManagerDep,
):
    """Convert an image to grayscale."""
    path = await asyncio.to_thread(
        service.process_image_edit, image_name, service.apply_grayscale, image_name
    )
    return EditResponse(path=path)


@router.post("/rotate", response_model=EditResponse)
@limiter.limit("15/minute")
async def rotate_image(
    request: Request,
    image_name: str,
    rotate_params: RotateEditRequest,
    service: EditManagerDep,
):
    """Rotate an image by the given degrees."""
    path = await asyncio.to_thread(
        service.process_image_edit,
        image_name,
        service.apply_rotation,
        image_name,
        rotate_params.degrees,
        rotate_params.expand,
    )
    return EditResponse(path=path)


@router.post("/blur", response_model=EditResponse)
@limiter.limit("10/minute")
async def blur_image(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    radius: float = Query(2.0, gt=0, description="The radius of the blur effect (must be greater than 0)."),
):
    """Apply a Gaussian blur."""
    path = await asyncio.to_thread(
        service.process_image_edit, image_name, service.apply_blur, image_name, radius
    )
    return EditResponse(path=path)


@router.post("/sharpen", response_model=EditResponse)
@limiter.limit("10/minute")
async def sharpen_image(
    request: Request,
    image_name: str,
    sharpen_params: SharpenEditRequest,
    service: EditManagerDep,
):
    """Sharpen an image using an unsharp mask."""
    path = await asyncio.to_thread(
        service.process_image_edit,
        image_name,
        service.apply_sharpen,
        image_name,
        sharpen_params.factor,
        sharpen_params.radius,
        sharpen_params.threshold,
    )
    return EditResponse(path=path)


@router.post("/brightness", response_model=EditResponse)
@limiter.limit("20/minute")
async def adjust_brightness(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    factor: float = Query(..., gt=0, description="The factor by which to adjust brightness (must be greater than 0)."),
):
    """Adjust image brightness (1.0 = no change)."""
    path = await asyncio.to_thread(
        service.process_image_edit, image_name, service.apply_brightness, image_name, factor
    )
    return EditResponse(path=path)


@router.post("/contrast", response_model=EditResponse)
@limiter.limit("20/minute")
async def adjust_contrast(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    factor: float = Query(..., gt=0, description="The factor by which to adjust contrast (must be greater than 0)."),
):
    """Adjust image contrast (1.0 = no change)."""
    path = await asyncio.to_thread(
        service.process_image_edit, image_name, service.apply_contrast, image_name, factor
    )
    return EditResponse(path=path)
