from fastapi import APIRouter, Depends, Query, Request
from typing import Annotated
from app.managers.edit_manager import EditManager, get_edit_manager
from app.schemas.editing.editing_requests import RotateEditRequest, SharpenEditRequest
from app.schemas.editing.editing_responses import EditResponse
from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger

# Initialize logger
logger = get_logger("editing_routes")

router = APIRouter(prefix="/images/edit", tags=["Image Editing"])

# Dependency for EditManager
EditManagerDep = Annotated[EditManager, Depends(get_edit_manager)]

# Route to resize the image
@router.post("/resize", response_model=EditResponse)
@limiter.limit("10/minute")
def resize_image(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    width: int = Query(..., gt=0, description="The target width for resizing (must be greater than 0)."),
    height: int = Query(..., gt=0, description="The target height for resizing (must be greater than 0)."),
):
    """
    Resize the image to the specified width and height.

    - **Parameters**:
        - **image_name**: The name of the image to be resized.
        - **width**: The target width for resizing (must be greater than 0).
        - **height**: The target height for resizing (must be greater than 0).

    - **Returns**: 
        - An **EditResponse** containing the path to the resized image.

    """
    path = service.process_image_edit(image_name, service.apply_resize, image_name, width, height)
    return EditResponse(path=path)

# Route to convert image to grayscale
@router.post("/grayscale", response_model=EditResponse)
@limiter.limit("20/minute")
def convert_to_grayscale(
    request: Request,
    image_name: str,
    service: EditManagerDep,
):
    """
    Convert the image to grayscale.

    - **Parameters**:
        - **image_name**: The name of the image to be converted.

    - **Returns**: 
        - An **EditResponse** containing the path to the grayscale image.
    """
    path = service.process_image_edit(image_name, service.apply_grayscale, image_name)
    return EditResponse(path=path)

# Route to rotate image
@router.post("/rotate", response_model=EditResponse)
@limiter.limit("15/minute")
def rotate_image(
    request: Request,
    image_name: str,
    rotate_params: RotateEditRequest,
    service: EditManagerDep,
):
    """
    Rotate the image by the specified degrees and expansion settings.

    - **Parameters**:
        - **image_name**: The name of the image to be rotated.
        - **rotate_params**: The parameters for rotating the image (degrees and expansion).

    - **Returns**: 
        - An **EditResponse** containing the path to the rotated image.
    """
    path = service.process_image_edit(image_name, service.apply_rotation, image_name, rotate_params.degrees, rotate_params.expand)
    return EditResponse(path=path)

# Route to apply blur to image
@router.post("/blur", response_model=EditResponse)
@limiter.limit("10/minute")
def blur_image(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    radius: float = Query(2.0, gt=0, description="The radius of the blur effect (must be greater than 0)."),
):
    """
    Apply a blur effect to the image with a specified radius.

    - **Parameters**:
        - **image_name**: The name of the image to be blurred.
        - **radius**: The radius of the blur effect (must be greater than 0).

    - **Returns**: 
        - An **EditResponse** containing the path to the blurred image.
    """
    path = service.process_image_edit(image_name, service.apply_blur, image_name, radius)
    return EditResponse(path=path)

# Route to sharpen image
@router.post("/sharpen", response_model=EditResponse)
@limiter.limit("10/minute")
def sharpen_image(
    request: Request,
    image_name: str,
    sharpen_params: SharpenEditRequest,
    service: EditManagerDep,
):
    """
    Sharpen the image with the specified parameters (factor, radius, threshold).

    - **Parameters**:
        - **image_name**: The name of the image to be sharpened.
        - **sharpen_params**: The sharpening parameters (factor, radius, threshold).

    - **Returns**: 
        - An **EditResponse** containing the path to the sharpened image.
    """
    path = service.process_image_edit(image_name, service.apply_sharpen, image_name, sharpen_params.factor, sharpen_params.radius, sharpen_params.threshold)
    return EditResponse(path=path)

# Route to adjust brightness of image
@router.post("/brightness", response_model=EditResponse)
@limiter.limit("20/minute")
def adjust_brightness(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    factor: float = Query(..., gt=0, description="The factor by which to adjust brightness (must be greater than 0)."),
):
    """
    Adjust the brightness of the image by a specified factor.

    - **Parameters**:
        - **image_name**: The name of the image to adjust brightness.
        - **factor**: The factor by which to adjust brightness (must be greater than 0).

    - **Returns**: 
        - An **EditResponse** containing the path to the brightness-adjusted image.
    """
    path = service.process_image_edit(image_name, service.apply_brightness, image_name, factor)
    return EditResponse(path=path)

# Route to adjust contrast of image
@router.post("/contrast", response_model=EditResponse)
@limiter.limit("20/minute")
def adjust_contrast(
    request: Request,
    image_name: str,
    service: EditManagerDep,
    factor: float = Query(..., gt=0, description="The factor by which to adjust contrast (must be greater than 0)."),
):
    """
    Adjust the contrast of the image by a specified factor.

    - **Parameters**:
        - **image_name**: The name of the image to adjust contrast.
        - **factor**: The factor by which to adjust contrast (must be greater than 0).

    - **Returns**: 
        - An **EditResponse** containing the path to the contrast-adjusted image.
    """
    path = service.process_image_edit(image_name, service.apply_contrast, image_name, factor)
    return EditResponse(path=path)

