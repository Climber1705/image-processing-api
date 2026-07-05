import asyncio
from typing import Annotated

from fastapi import APIRouter, Request, UploadFile, HTTPException, status, Depends, Query

from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger
from app.dependencies.services import get_image_service
from app.dependencies.validation import get_simple_image_validator
from app.media.service import ImageService
from app.media.requests import (
    CreateImageForm,
    FolderFilterQuery,
    ImageFolderQuery,
    ListImagesQuery,
    MoveImageRequest,
    get_create_image_form,
)
from app.media.schema import (
    ImageDetailResponse,
    ImageListItem,
    ImageMetadata,
    ImageResponse,
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
    _: Request,
    file: UploadFile,
    form: CreateImageForm = Depends(get_create_image_form),
    image_service: ImageService = Depends(get_image_service),
    validator: SimpleImageValidator = Depends(get_simple_image_validator),
):
    """Upload an image file with optional custom filename and output format."""
    try:
        await asyncio.to_thread(validator.validate, file)

        logger.info(
            f"Uploading image: {file.filename} as {form.filename or file.filename} with format {form.format}"
        )
        file_path, metadata = await asyncio.to_thread(
            image_service.save_uploaded_image, file, form.filename, form.format
        )
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
    _: Request,
    query: Annotated[ListImagesQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """List images with optional folder filter and pagination."""
    logger.info(f"Fetching image list from folder: {query.folder}, limit={query.limit}, offset={query.offset}")
    return await asyncio.to_thread(image_service.list_images, query.folder, query.limit, query.offset)


@router.delete("", response_model=StatusResponse)
@limiter.limit("2/hour")
async def delete_all_images(
    _: Request,
    query: Annotated[FolderFilterQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """Delete all images in a folder. Irreversible."""
    logger.warning(f"Clearing all images in folder: {query.folder}")
    return await asyncio.to_thread(image_service.delete_all_images, query.folder)


@router.get("/{filename}", response_model=ImageDetailResponse)
@limiter.limit("30/minute")
async def get_image(
    _: Request,
    filename: str,
    query: Annotated[ImageFolderQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """Get metadata for a single image."""
    logger.info(f"Fetching details for image: {filename} in folder: {query.folder}")
    return await asyncio.to_thread(image_service.get_image_by_id, filename, query.folder)


@router.delete("/{filename}", response_model=StatusResponse)
@limiter.limit("10/minute")
async def delete_image(
    _: Request,
    filename: str,
    query: Annotated[ImageFolderQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """Delete a single image by name."""
    logger.info(f"Deleting image: {filename} from folder: {query.folder}")
    return await asyncio.to_thread(image_service.delete_image, filename, query.folder)


@router.patch("/{filename}", response_model=ImageDetailResponse)
@limiter.limit("20/minute")
async def update_image(
    _: Request,
    filename: str,
    move_params: MoveImageRequest,
    image_service: ImageService = Depends(get_image_service),
):
    """Move an image between storage folders."""
    logger.info(f"Moving image: {filename} from {move_params.source_folder} to {move_params.target_folder}")
    return await asyncio.to_thread(
        image_service.move_image, filename, move_params.source_folder, move_params.target_folder
    )
