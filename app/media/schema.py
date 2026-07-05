from typing import Optional

from pydantic import BaseModel, Field


class MoveImageRequest(BaseModel):
    source_folder: str = Field("uploaded", description="Current folder name")
    target_folder: str = Field("edited", description="Target folder name")


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


class ImageDimensionsResponse(BaseModel):
    width: int
    height: int
