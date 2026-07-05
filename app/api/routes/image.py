import asyncio
from typing import Annotated

from fastapi import APIRouter, Request, UploadFile, status, Depends, Query

from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger
from app.dependencies.services import get_image_service
from app.media.api import (
    CreateImageForm,
    FolderFilterQuery,
    ImageDetailResponse,
    ImageFolderQuery,
    ImageListItem,
    ImageResponse,
    ListImagesQuery,
    MoveImageRequest,
    StatusResponse,
    get_create_image_form,
)
from app.media.utils.mappers import (
    to_delete_status_response,
    to_detail_response,
    to_list_item,
    to_status_response,
    to_upload_response,
)
from app.media.service import ImageService
from app.validation.validator import validate_upload

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
    form: CreateImageForm = Depends(get_create_image_form),
    image_service: ImageService = Depends(get_image_service),
):
    """Upload an image file with optional custom filename and output format."""
    await asyncio.to_thread(validate_upload, file)
    result = await asyncio.to_thread(
        image_service.upload_image,
        file,
        form.filename,
        form.format,
    )
    return to_upload_response(result)


@router.get("", response_model=list[ImageListItem])
@limiter.limit("60/minute")
async def get_images(
    request: Request,
    query: Annotated[ListImagesQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """List images with optional folder filter and pagination."""
    images = await asyncio.to_thread(
        image_service.get_images,
        query.folder,
        query.limit,
        query.offset,
    )
    return [to_list_item(image) for image in images]


@router.delete("", response_model=StatusResponse)
@limiter.limit("2/hour")
async def delete_images(
    request: Request,
    query: Annotated[FolderFilterQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """Delete all images in a folder. Irreversible."""
    result = await asyncio.to_thread(
        image_service.delete_images,
        query.folder,
    )
    return to_status_response(result)


@router.get("/{filename}", response_model=ImageDetailResponse)
@limiter.limit("30/minute")
async def get_image(
    request: Request,
    filename: str,
    query: Annotated[ImageFolderQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """Get metadata for a single image."""
    image = await asyncio.to_thread(
        image_service.get_image_by_filename,
        filename,
        query.folder,
    )
    return to_detail_response(image)


@router.delete("/{filename}", response_model=StatusResponse)
@limiter.limit("10/minute")
async def delete_image(
    request: Request,
    filename: str,
    query: Annotated[ImageFolderQuery, Query()],
    image_service: ImageService = Depends(get_image_service),
):
    """Delete a single image by name."""
    result = await asyncio.to_thread(
        image_service.delete_image,
        filename,
        query.folder,
    )
    return to_delete_status_response(result)


@router.patch("/{filename}", response_model=ImageDetailResponse)
@limiter.limit("20/minute")
async def move_image(
    request: Request,
    filename: str,
    move_params: MoveImageRequest,
    image_service: ImageService = Depends(get_image_service),
):
    """Move an image between storage folders."""
    image = await asyncio.to_thread(
        image_service.move_image,
        filename,
        move_params.source_folder,
        move_params.target_folder,
    )
    return to_detail_response(image)
