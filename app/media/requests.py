from typing import Literal

from fastapi import Form
from pydantic import BaseModel, Field, field_validator, model_validator

from app.media.enums import FolderFilter, ImageFolder

ImageFormat = Literal["JPEG", "JPG", "PNG", "GIF", "BMP", "TIFF", "WEBP"]


class CreateImageForm(BaseModel):
    filename: str | None = Field(
        default=None,
        max_length=255,
        description="Optional display filename (extension is derived from format).",
    )
    format: ImageFormat = Field(
        default="JPEG",
        description="Output image format.",
    )

    @field_validator("format", mode="before")
    @classmethod
    def normalize_format(cls, value: str) -> str:
        return value.upper() if isinstance(value, str) else value

    @field_validator("filename")
    @classmethod
    def strip_filename(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ListImagesQuery(BaseModel):
    folder: FolderFilter = Field(
        default=FolderFilter.ALL,
        description="Filter images by folder (defaults to 'all').",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Limit the number of images to retrieve (between 1 and 1000).",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset for pagination, skip the first N images.",
    )


class FolderFilterQuery(BaseModel):
    folder: FolderFilter = Field(
        default=FolderFilter.ALL,
        description="The folder to filter by (defaults to 'all').",
    )


class ImageFolderQuery(BaseModel):
    folder: ImageFolder = Field(
        default=ImageFolder.UPLOADED,
        description="The folder containing the image (defaults to 'uploaded').",
    )


class MoveImageRequest(BaseModel):
    source_folder: ImageFolder = Field(
        default=ImageFolder.UPLOADED,
        description="Current folder name.",
    )
    target_folder: ImageFolder = Field(
        default=ImageFolder.EDITED,
        description="Target folder name.",
    )

    @model_validator(mode="after")
    def folders_must_differ(self) -> "MoveImageRequest":
        if self.source_folder == self.target_folder:
            raise ValueError("Source and target folders cannot be the same")
        return self


def get_create_image_form(
    filename: str | None = Form(default=None),
    format: ImageFormat = Form(default="JPEG"),
) -> CreateImageForm:
    return CreateImageForm(filename=filename, format=format)
