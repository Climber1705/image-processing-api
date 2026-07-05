import asyncio
from fastapi import APIRouter, Request, UploadFile, HTTPException, status, Depends, Query

from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger
from app.dependencies.services import get_image_service
from app.dependencies.validation import get_simple_image_validator
from app.media.service import ImageService
from app.media.schema import (
    ImageDetailResponse,
    ImageListItem,
    ImageMetadata,
    ImageResponse,
    MoveImageRequest,
    StatusResponse,
)
from app.validation.simple_validator import SimpleImageValidator

logger = get_logger("image_routes")

router = APIRouter(
    prefix="/images",
    tags=["Images"],
    responses={404: {"description": "Not found"}},
)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ImageResponse)
@limiter.limit("10/minute")
async def create_image(
    request: Request,
    file: UploadFile,
    filename: str | None = None,
    format: str = "JPEG",
    image_service: ImageService = Depends(get_image_service),
    validator: SimpleImageValidator = Depends(get_simple_image_validator),
):
    """Upload an image file with optional custom filename and output format."""
    try:
        await asyncio.to_thread(validator.validate, file)
        await asyncio.to_thread(validator.validate_format, format)

        logger.info(f"Uploading image: {file.filename} as {filename or file.filename} with format {format}")
        file_path, metadata = await asyncio.to_thread(image_service.save_uploaded_image, file, filename, format)
        logger.info(f"Image uploaded successfully: {file_path}")
        return ImageResponse(
            status="success",
            path=file_path,
            metadata=ImageMetadata(
                format=metadata["format"],
                mode=metadata["mode"],
                width=metadata["width"],
                height=metadata["height"],
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {file.filename} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=list[ImageListItem])
@limiter.limit("60/minute")
async def list_images(
    request: Request,
    image_service: ImageService = Depends(get_image_service),
    folder: str = Query("all", description="Filter images by folder (defaults to 'all')."),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of images to retrieve (between 1 and 1000)."),
    offset: int = Query(0, ge=0, description="Offset for pagination, skip the first N images."),
):
    """List images with optional folder filter and pagination."""
    logger.info(f"Fetching image list from folder: {folder}, limit={limit}, offset={offset}")
    return await asyncio.to_thread(image_service.list_images, folder, limit, offset)


@router.delete("", response_model=StatusResponse)
@limiter.limit("2/hour")
async def delete_all_images(
    request: Request,
    image_service: ImageService = Depends(get_image_service),
    folder: str = Query("all", description="The folder from which to delete all images (defaults to 'all')."),
):
    """Delete all images in a folder. Irreversible."""
    logger.warning(f"Clearing all images in folder: {folder}")
    return await asyncio.to_thread(image_service.delete_all_images, folder)


@router.get("/{filename}", response_model=ImageDetailResponse)
@limiter.limit("30/minute")
async def get_image(
    request: Request,
    filename: str,
    image_service: ImageService = Depends(get_image_service),
    folder: str = Query("uploaded", description="The folder to fetch the image from (defaults to 'uploaded')."),
):
    """Get metadata for a single image."""
    logger.info(f"Fetching details for image: {filename} in folder: {folder}")
    return await asyncio.to_thread(image_service.get_image_by_id, filename, folder)


@router.delete("/{filename}", response_model=StatusResponse)
@limiter.limit("10/minute")
async def delete_image(
    request: Request,
    filename: str,
    image_service: ImageService = Depends(get_image_service),
    folder: str = Query("uploaded", description="The folder from which to delete the image (defaults to 'uploaded')."),
):
    """Delete a single image by name."""
    logger.info(f"Deleting image: {filename} from folder: {folder}")
    return await asyncio.to_thread(image_service.delete_image, filename, folder)


@router.patch("/{filename}", response_model=ImageDetailResponse)
@limiter.limit("20/minute")
async def update_image(
    request: Request,
    filename: str,
    move_params: MoveImageRequest,
    image_service: ImageService = Depends(get_image_service),
):
    """Move an image between storage folders."""
    logger.info(f"Moving image: {filename} from {move_params.source_folder} to {move_params.target_folder}")
    return await asyncio.to_thread(
        image_service.move_image, filename, move_params.source_folder, move_params.target_folder
    )
