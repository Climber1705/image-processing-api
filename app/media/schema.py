from typing import Optional

from pydantic import BaseModel

from app.media.requests import MoveImageRequest

__all__ = [
    "ImageDetailResponse",
    "ImageListItem",
    "ImageMetadata",
    "ImageResponse",
    "MoveImageRequest",
    "StatusResponse",
]


class StatusResponse(BaseModel):
    status: str


class ImageMetadata(BaseModel):
    format: str
    mode: str
    width: int
    height: int


class ImageResponse(BaseModel):
    status: str
    path: str
    metadata: ImageMetadata


class ImageListItem(BaseModel):
    filename: str
    format: str
    mode: str
    width: int
    height: int
    size_bytes: int
    path: str
    url: Optional[str] = None
    folder: str


class ImageDetailResponse(BaseModel):
    filename: str
    format: str
    mode: str
    width: int
    height: int
    size_bytes: int
    path: str
    url: Optional[str] = None
