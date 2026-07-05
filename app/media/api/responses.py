
from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: str
    message: str | None = None


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
    url: str | None = None
    folder: str


class ImageDetailResponse(BaseModel):
    filename: str
    format: str
    mode: str
    width: int
    height: int
    size_bytes: int
    path: str
    url: str | None = None
