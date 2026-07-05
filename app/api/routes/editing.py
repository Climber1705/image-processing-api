import asyncio
from fastapi import APIRouter, Depends, Query, Request

from app.core.rate_limiting import limiter
from app.dependencies.services import get_image_edit_service
from app.editing.api import EditResponse, RotateEditRequest, SharpenEditRequest
from app.editing.api.mappers import to_edit_response
from app.editing.service import ImageEditService

router = APIRouter(prefix="/images/{filename}/edits", tags=["Editing"])


@router.post("/resize", response_model=EditResponse)
@limiter.limit("10/minute")
async def resize_image(
    request: Request,
    filename: str,
    edit_service: ImageEditService = Depends(get_image_edit_service),
    width: int = Query(..., gt=0, description="The target width for resizing (must be greater than 0)."),
    height: int = Query(..., gt=0, description="The target height for resizing (must be greater than 0)."),
):
    """Resize an image to the given width and height."""
    result = await asyncio.to_thread(
        edit_service.resize_image,
        filename,
        width,
        height,
    )
    return to_edit_response(result)


@router.post("/grayscale", response_model=EditResponse)
@limiter.limit("20/minute")
async def convert_to_grayscale(
    request: Request,
    filename: str,
    edit_service: ImageEditService = Depends(get_image_edit_service),
):
    """Convert an image to grayscale."""
    result = await asyncio.to_thread(
        edit_service.convert_to_grayscale,
        filename,
    )
    return to_edit_response(result)


@router.post("/rotate", response_model=EditResponse)
@limiter.limit("15/minute")
async def rotate_image(
    request: Request,
    filename: str,
    rotate_params: RotateEditRequest,
    edit_service: ImageEditService = Depends(get_image_edit_service),
):
    """Rotate an image by the given degrees."""
    result = await asyncio.to_thread(
        edit_service.rotate_image,
        filename,
        rotate_params.degrees,
        rotate_params.expand,
    )
    return to_edit_response(result)


@router.post("/blur", response_model=EditResponse)
@limiter.limit("10/minute")
async def blur_image(
    request: Request,
    filename: str,
    edit_service: ImageEditService = Depends(get_image_edit_service),
    radius: float = Query(2.0, gt=0, description="The radius of the blur effect (must be greater than 0)."),
):
    """Apply a Gaussian blur."""
    result = await asyncio.to_thread(
        edit_service.blur_image,
        filename,
        radius,
    )
    return to_edit_response(result)


@router.post("/sharpen", response_model=EditResponse)
@limiter.limit("10/minute")
async def sharpen_image(
    request: Request,
    filename: str,
    sharpen_params: SharpenEditRequest,
    edit_service: ImageEditService = Depends(get_image_edit_service),
):
    """Sharpen an image using an unsharp mask."""
    result = await asyncio.to_thread(
        edit_service.sharpen_image,
        filename,
        sharpen_params.factor,
        sharpen_params.radius,
        sharpen_params.threshold,
    )
    return to_edit_response(result)


@router.post("/brightness", response_model=EditResponse)
@limiter.limit("20/minute")
async def adjust_brightness(
    request: Request,
    filename: str,
    edit_service: ImageEditService = Depends(get_image_edit_service),
    factor: float = Query(..., gt=0, description="The factor by which to adjust brightness (must be greater than 0)."),
):
    """Adjust image brightness (1.0 = no change)."""
    result = await asyncio.to_thread(
        edit_service.adjust_brightness,
        filename,
        factor,
    )
    return to_edit_response(result)


@router.post("/contrast", response_model=EditResponse)
@limiter.limit("20/minute")
async def adjust_contrast(
    request: Request,
    filename: str,
    edit_service: ImageEditService = Depends(get_image_edit_service),
    factor: float = Query(..., gt=0, description="The factor by which to adjust contrast (must be greater than 0)."),
):
    """Adjust image contrast (1.0 = no change)."""
    result = await asyncio.to_thread(
        edit_service.adjust_contrast,
        filename,
        factor,
    )
    return to_edit_response(result)
