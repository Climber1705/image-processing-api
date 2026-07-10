from app.media.api.responses import (
    ImageDetailResponse,
    ImageListItem,
    ImageMetadata,
    ImageResponse,
    StatusResponse,
)
from app.media.domain.dtos import (
    DeleteImageResultDTO,
    ImageDTO,
    OperationStatusDTO,
    SaveImageResultDTO,
)
from app.models.image import ImageRecord


def record_to_dto(record: ImageRecord) -> ImageDTO:
    return ImageDTO(
        id=record.id,
        filename=record.filename,
        format=record.format,
        mode=record.mode,
        width=record.width,
        height=record.height,
        size_bytes=record.size_bytes,
        path=record.path,
        folder=record.folder,
    )


def to_list_item(dto: ImageDTO) -> ImageListItem:
    return ImageListItem(
        filename=dto.filename,
        format=dto.format,
        mode=dto.mode,
        width=dto.width,
        height=dto.height,
        size_bytes=dto.size_bytes,
        path=dto.path,
        folder=dto.folder,
    )


def to_detail_response(dto: ImageDTO) -> ImageDetailResponse:
    return ImageDetailResponse(
        filename=dto.filename,
        format=dto.format,
        mode=dto.mode,
        width=dto.width,
        height=dto.height,
        size_bytes=dto.size_bytes,
        path=dto.path,
    )


def to_upload_response(result: SaveImageResultDTO) -> ImageResponse:
    return ImageResponse(
        status="success",
        path=result.path,
        metadata=ImageMetadata(
            format=result.image.format,
            mode=result.image.mode,
            width=result.image.width,
            height=result.image.height,
        ),
    )


def to_status_response(dto: OperationStatusDTO) -> StatusResponse:
    return StatusResponse(status=dto.status, message=dto.message)


def to_delete_status_response(dto: DeleteImageResultDTO) -> StatusResponse:
    return StatusResponse(status=dto.status, message=dto.message)
