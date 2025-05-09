from fastapi import APIRouter, Request, UploadFile, HTTPException, status, Depends, Query
from typing import Optional, List, Annotated

from app.schemas.image.image_responses import (
    ImageDetailResponse,
    ImageDimensionsResponse,
    ImageListItem,
    ImageResponse,
    StatusResponse
)
from app.schemas.image.image_requests import MoveImageRequest
from app.managers.image_manager import ImageManager, get_image_manager
from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger

# Initialize logger
logger = get_logger("image_routes")

# Create the router for image CRUD operations
router = APIRouter(
    prefix="/images",
    tags=["CRUD Images"],
    responses={404: {"description": "Not found"}},
)

# Dependency injection for image manager
ImageManagerDep = Annotated[ImageManager, Depends(get_image_manager)]

# Upload an image file and return its metadata
@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=ImageResponse)
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    service: ImageManagerDep,
    file: UploadFile,
    filename: Optional[str] = None,
    format: str = "JPEG"
):
    """
    Upload an image file.

    This endpoint allows the user to upload an image file. Optionally, the user can provide a filename and choose
    the desired format (default is JPEG). The endpoint returns the metadata of the uploaded image.
    
    **Parameters:**
    - **file**: The image file being uploaded.
    - **filename**: (Optional) The desired filename for the uploaded image. If not provided, the original filename is used.
    - **format**: (Optional) The format of the uploaded image. Default is "JPEG".
    
    **Returns:**
    - An **ImageResponse** containing the status, file path, and metadata of the uploaded image.
    """
    try:
        logger.info(f"Uploading image: {file.filename} as {filename or file.filename} with format {format}")
        file_path = service.save_uploaded_image(file, filename, format)
        metadata = service.get_image_metadata(file_path)
        logger.info(f"Image uploaded successfully: {file_path}")
        return ImageResponse(
            status="success",
            path=file_path,
            metadata=metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {file.filename} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Get a list of images with optional filtering, pagination, and limits
@router.get("/", response_model=List[ImageListItem])
@limiter.limit("60/minute")
async def get_images(
    request: Request,
    service: ImageManagerDep,
    folder: str = Query("all", description="Filter images by folder (defaults to 'all')."),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of images to retrieve (between 1 and 1000)."),
    offset: int = Query(0, ge=0, description="Offset for pagination, skip the first N images.")
):
    """
    Get a list of images with optional filtering, pagination, and limits.

    This endpoint retrieves a list of images, allowing the user to filter by folder, specify the maximum number of
    images to retrieve (pagination), and skip a certain number of images.

    **Parameters:**
    - **folder**: The folder to fetch images from. Defaults to 'all'.
    - **limit**: The maximum number of images to return. Defaults to 100, max 1000.
    - **offset**: The number of images to skip, useful for pagination.

    **Returns:**
    - A list of **ImageListItem** objects containing metadata of the images.
    """
    logger.info(f"Fetching image list from folder: {folder}, limit={limit}, offset={offset}")
    return service.list_images(folder, limit, offset)

# Get detailed metadata for a specific image
@router.get("/{image_name}/detail", response_model=ImageDetailResponse)
@limiter.limit("30/minute")
async def get_image(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    folder: str = Query("uploaded", description="The folder to fetch the image from (defaults to 'uploaded')."),
):
    """
    Get detailed metadata of a specific image by its name.

    This endpoint retrieves metadata for a specified image, including dimensions, format, and other details.
    
    **Parameters:**
    - **image_name**: The name of the image to retrieve.
    - **folder**: The folder containing the image. Defaults to 'uploaded'.

    **Returns:**
    - An **ImageDetailResponse** containing detailed metadata of the image.
    """
    logger.info(f"Fetching details for image: {image_name} in folder: {folder}")
    return service.get_image_by_id(image_name, folder)

# Get the dimensions (width and height) of an image
@router.get("/{image_name}/metadata/dimensions", response_model=ImageDimensionsResponse)
@limiter.limit("20/minute")
async def get_dimensions(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    folder: str = Query("uploaded", description="The folder containing the image (defaults to 'uploaded')."),
):
    """
    Get the dimensions (width and height) of a specific image.

    This endpoint retrieves only the dimensions of the image, which can be useful for display or processing.
    
    **Parameters:**
    - **image_name**: The name of the image to retrieve dimensions for.
    - **folder**: The folder where the image is stored. Defaults to 'uploaded'.

    **Returns:**
    - An **ImageDimensionsResponse** containing the width and height of the image.
    """
    logger.info(f"Fetching dimensions for image: {image_name} in folder: {folder}")
    image_path = service.get_image_path(image_name, folder)
    width, height = service.get_image_dimensions(image_path)
    return ImageDimensionsResponse(width=width, height=height)

# Delete a specific image by its name
@router.delete("/{image_name}/delete", response_model=StatusResponse)
@limiter.limit("10/minute")
async def delete_image(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    folder: str = Query("uploaded", description="The folder from which to delete the image (defaults to 'uploaded')."),
):
    """
    Delete a specific image identified by its name.

    This endpoint allows the user to delete an image from a specified folder.
    
    **Parameters:**
    - **image_name**: The name of the image to delete.
    - **folder**: The folder from which to delete the image. Defaults to 'uploaded'.

    **Returns:**
    - A **StatusResponse** indicating success or failure.
    """
    logger.info(f"Deleting image: {image_name} from folder: {folder}")
    return service.delete_image(image_name, folder)

# Move an image from one folder to another
@router.post("/{image_name}/move", response_model=ImageDetailResponse)
@limiter.limit("20/minute")
async def move_image(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    move_params: MoveImageRequest,
):
    """
    Move an image from one folder to another.

    This endpoint moves an image from one folder to another, updating its location.
    
    **Parameters:**
    - **image_name**: The name of the image to move.
    - **move_params**: A request object containing the source and target folders for the move.

    **Returns:**
    - A **StatusResponse** indicating success or failure.
    """
    logger.info(f"Moving image: {image_name} from {move_params.source_folder} to {move_params.target_folder}")
    return service.move_image(image_name, move_params.source_folder, move_params.target_folder)

# Delete all images in a specified folder
@router.delete("/images/clear_all", response_model=StatusResponse)
@limiter.limit("2/hour")
async def clear_images(
    request: Request,
    service: ImageManagerDep,
    folder: str = Query("all", description="The folder from which to delete all images (defaults to 'all')."),
):
    """
    Delete all images in a specified folder.

    This endpoint allows the user to delete all images in a folder, useful for batch cleanup.
    
    **Parameters:**
    - **folder**: The folder to clear. Defaults to 'all'.

    **Returns:**
    - A **StatusResponse** indicating success or failure.
    """
    logger.warning(f"Clearing all images in folder: {folder}")
    return service.delete_all_images(folder)
