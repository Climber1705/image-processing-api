from fastapi import APIRouter, Request, UploadFile, HTTPException, status, Depends, Query
from typing import Optional, List, Annotated
import asyncio

from app.schemas.image.image_responses import (
    ImageDetailResponse,
    ImageDimensionsResponse,
    ImageListItem,
    ImageResponse,
    StatusResponse,
)
from app.schemas.image.image_requests import MoveImageRequest
from app.managers.image_manager import ImageManager, get_image_manager
from app.utils.validator.simple_validator import SimpleImageValidator, get_simple_image_validator
from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger

logger = get_logger("image_routes")

router = APIRouter(
    prefix="/images",
    tags=["CRUD Images"],
    responses={404: {"description": "Not found"}},
)

ImageManagerDep = Annotated[ImageManager, Depends(get_image_manager)]
ImageValidatorDep = Annotated[SimpleImageValidator, Depends(get_simple_image_validator)]


@router.post("/upload", status_code=status.HTTP_201_CREATED, response_model=ImageResponse)
@limiter.limit("10/minute")
async def upload_image(
    request: Request,
    service: ImageManagerDep,
    validator: ImageValidatorDep,
    file: UploadFile,
    filename: Optional[str] = None,
    format: str = "JPEG",
):
    """Upload an image file with optional custom filename and output format."""
    try:
        await asyncio.to_thread(validator.validate, file)
        await asyncio.to_thread(validator.validate_format, format)

        logger.info(f"Uploading image: {file.filename} as {filename or file.filename} with format {format}")
        file_path = await asyncio.to_thread(service.save_uploaded_image, file, filename, format)
        metadata = await asyncio.to_thread(service.get_image_metadata, file_path)
        logger.info(f"Image uploaded successfully: {file_path}")
        return ImageResponse(status="success", path=file_path, metadata=metadata)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {file.filename} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=List[ImageListItem])
@limiter.limit("60/minute")
async def get_images(
    request: Request,
    service: ImageManagerDep,
    folder: str = Query("all", description="Filter images by folder (defaults to 'all')."),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of images to retrieve (between 1 and 1000)."),
    offset: int = Query(0, ge=0, description="Offset for pagination, skip the first N images."),
):
    """List images with optional folder filter and pagination."""
    logger.info(f"Fetching image list from folder: {folder}, limit={limit}, offset={offset}")
    return await asyncio.to_thread(service.list_images, folder, limit, offset)


@router.get("/{image_name}/detail", response_model=ImageDetailResponse)
@limiter.limit("30/minute")
async def get_image(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    folder: str = Query("uploaded", description="The folder to fetch the image from (defaults to 'uploaded')."),
):
    """Get metadata for a single image."""
    logger.info(f"Fetching details for image: {image_name} in folder: {folder}")
    return await asyncio.to_thread(service.get_image_by_id, image_name, folder)


@router.get("/{image_name}/metadata/dimensions", response_model=ImageDimensionsResponse)
@limiter.limit("20/minute")
async def get_dimensions(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    folder: str = Query("uploaded", description="The folder containing the image (defaults to 'uploaded')."),
):
    """Get width and height for an image."""
    logger.info(f"Fetching dimensions for image: {image_name} in folder: {folder}")
    image_path = await asyncio.to_thread(service.get_image_path, image_name, folder)
    width, height = await asyncio.to_thread(service.get_image_dimensions, image_path)
    return ImageDimensionsResponse(width=width, height=height)


@router.delete("/{image_name}/delete", response_model=StatusResponse)
@limiter.limit("10/minute")
async def delete_image(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    folder: str = Query("uploaded", description="The folder from which to delete the image (defaults to 'uploaded')."),
):
    """Delete a single image by name."""
    logger.info(f"Deleting image: {image_name} from folder: {folder}")
    return await asyncio.to_thread(service.delete_image, image_name, folder)


@router.post("/{image_name}/move", response_model=ImageDetailResponse)
@limiter.limit("20/minute")
async def move_image(
    request: Request,
    service: ImageManagerDep,
    image_name: str,
    move_params: MoveImageRequest,
):
    """Move an image between storage folders."""
    logger.info(f"Moving image: {image_name} from {move_params.source_folder} to {move_params.target_folder}")
    return await asyncio.to_thread(
        service.move_image, image_name, move_params.source_folder, move_params.target_folder
    )


@router.delete("/clear_all", response_model=StatusResponse)
@limiter.limit("2/hour")
async def clear_images(
    request: Request,
    service: ImageManagerDep,
    folder: str = Query("all", description="The folder from which to delete all images (defaults to 'all')."),
):
    """Delete all images in a folder. Irreversible."""
    logger.warning(f"Clearing all images in folder: {folder}")
    return await asyncio.to_thread(service.delete_all_images, folder)
