from typing import Dict, Tuple
from fastapi import HTTPException, UploadFile, status, Depends
import logging
import io

from app.utils.validator.base_validator import BaseImageValidator
from app.core.dependencies import get_format_extensions

logger = logging.getLogger("simple_validator")


class SimpleImageValidator(BaseImageValidator):
    def __init__(
        self,
        format_extensions: Dict[str, str],
        max_size_mb: int = 5,
        allowed_types: Tuple[str, ...] = ("image/jpeg", "image/png"),
    ):
        self.format_extensions = format_extensions
        self.max_size = max_size_mb * 1024 * 1024
        self.allowed_types = allowed_types
        logger.info(
            "Initialized SimpleImageValidator with max size %d bytes and allowed types: %s",
            self.max_size,
            self.allowed_types,
        )

    def validate(self, image: UploadFile) -> None:
        try:
            logger.debug("Validating image with content type: %s", image.content_type)
            self.validate_type(image)
            self.validate_size(image)
        except HTTPException as e:
            logger.error("Validation failed: %s", e.detail)
            raise e

    def validate_type(self, image: UploadFile) -> None:
        if image.content_type not in self.allowed_types:
            logger.warning("Unsupported file type: %s", image.content_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type.",
            )
        logger.info("Validated image type: %s", image.content_type)

    def validate_size(self, image: UploadFile) -> None:
        current_position = image.file.tell()
        image.file.seek(0, io.SEEK_END)
        file_size = image.file.tell()
        image.file.seek(current_position)

        if file_size > self.max_size:
            logger.warning("File size too large: %d bytes, max allowed: %d bytes", file_size, self.max_size)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Max size is {} MB.".format(self.max_size // (1024 * 1024)),
            )
        logger.info("Validated image size: %d bytes", file_size)

    def validate_format(self, format: str) -> str:
        format = format.upper()
        if format not in self.format_extensions:
            supported_formats = ", ".join(self.format_extensions.keys())
            logger.warning("Unsupported format: %s. Supported formats: %s", format, supported_formats)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format: {format}. Supported formats: {supported_formats}",
            )
        logger.info("Validated image format: %s", format)
        return format

    def get_extension(self, format: str) -> str:
        format = self.validate_format(format)
        extension = self.format_extensions[format]
        logger.info("Retrieved file extension for format %s: %s", format, extension)
        return extension


def get_simple_image_validator(
    format_extensions: Dict[str, str] = Depends(get_format_extensions),
) -> SimpleImageValidator:
    logger.debug("Creating SimpleImageValidator instance with provided format extensions")
    return SimpleImageValidator(format_extensions=format_extensions)
