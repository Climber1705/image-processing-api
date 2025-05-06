from fastapi import APIRouter, Depends
from app.services.processing.processing_controller import ImageProcessing
from app.core.dependencies import get_image_processing

router = APIRouter(prefix="/process", tags=["Editing Images"])

@router.post("/resize/")
async def resize(
    image_id: str,
    width: int,
    height: int,
    service: ImageProcessing = Depends(get_image_processing),
) -> dict:
    
    """Resize an image to the specified width and height."""
    return service.resize_image(image_id, width, height)

@router.post("/grayscale/")
async def grayscale(
    image_id: str,
    service: ImageProcessing = Depends(get_image_processing),
) -> dict:
    """Convert an image to grayscale."""

    return service.convert_to_grayscale(image_id)

@router.post("/rotate/")
async def rotate(
    image_id: str,
    degrees: int,
    service: ImageProcessing = Depends(get_image_processing),
):
    return service.rotate_image(image_id, degrees)

@router.post("/crop/")
async def crop(
    image_id: str,
    left: int,
    upper: int,
    right: int,
    lower: int,
    service: ImageProcessing = Depends(get_image_processing),
):
    return service.crop_image(image_id, left, upper, right, lower)

@router.post("/blur/")
async def blur(
    image_id: str,
    radius: int, 
    service: ImageProcessing = Depends(get_image_processing),
):
    return service.blur_image(image_id, radius)

@router.post("/sharpen/")
async def sharpen(
    image_id: str,
    factor: float,
    radius: float,
    threshold: float,
    service: ImageProcessing = Depends(get_image_processing),
):
    return service.sharpen_image(image_id, factor, radius, threshold)


