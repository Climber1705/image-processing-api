from typing import Dict
from fastapi import HTTPException, UploadFile, status, Depends
from app.utils.validator.base_validator import BaseImageValidator
from app.core.dependencies import get_format_extensions
import logging

# Set up logger
logger = logging.getLogger("simple_validator")

class SimpleImageValidator(BaseImageValidator):
    """
    A simple image validator that checks image type, size, and format.
    
    - Validates that the image file type is within the allowed types (JPEG, PNG by default).
    - Ensures the image size does not exceed the maximum allowed size (default 5 MB).
    - Checks if the image format is supported (based on the provided format extensions).
    """

    def __init__(self, format_extensions: Dict[str, str], max_size_mb=5, allowed_types=("image/jpeg", "image/png")):
        """
        Initializes the SimpleImageValidator with allowed types, max size, and format extensions.

        @param format_extensions: A dictionary mapping image formats to their file extensions.
        @param max_size_mb: The maximum allowed file size in MB (default is 5 MB).
        @param allowed_types: A tuple of allowed MIME types (default is JPEG and PNG).
        """
        self.format_extensions = format_extensions
        self.max_size = max_size_mb * 1024 * 1024 
        self.allowed_types = allowed_types

        logger.info("Initialized SimpleImageValidator with max size %d bytes and allowed types: %s", self.max_size, self.allowed_types)

    def validate(self, image: UploadFile) -> None:
        """
        Validates the image by checking its type, size, and format.

        @param image: The image file to validate (FastAPI's UploadFile).
        
        Raises HTTPException if any validation fails.
        """
        try:
            logger.debug("Validating image with content type: %s", image.content_type)
            self.validate_type(image)
            self.validate_size(image)
        except HTTPException as e:
            logger.error("Validation failed: %s", e.detail)
            raise e

    def validate_type(self, image: UploadFile) -> None:
        """
        Validates the type of the image.

        @param image: The image file to validate.
        
        Raises HTTPException if the type is not allowed.
        """
        if image.content_type not in self.allowed_types:
            logger.warning("Unsupported file type: %s", image.content_type)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type."
            )
        logger.info("Validated image type: %s", image.content_type)

    def validate_size(self, image: UploadFile) -> None:
        """
        Validates the size of the image file.

        @param image: The image file to validate.
        
        Raises HTTPException if the file is too large.
        """
        if image.file.__sizeof__() > self.max_size:
            logger.warning("File size too large: %d bytes, max allowed: %d bytes", image.file.__sizeof__(), self.max_size)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Max size is {} MB.".format(self.max_size // (1024 * 1024))
            )
        logger.info("Validated image size: %d bytes", image.file.__sizeof__())

    def validate_format(self, format: str) -> str:
        """
        Validates the format of the image.

        @param format: The format of the image to validate (e.g., "JPEG").
        
        Returns the format if valid, raises HTTPException if not.
        """
        format = format.upper()
        if format not in self.format_extensions:
            supported_formats = ", ".join(self.format_extensions.keys())
            logger.warning("Unsupported format: %s. Supported formats: %s", format, supported_formats)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported image format: {format}. Supported formats: {supported_formats}"
            )
        logger.info("Validated image format: %s", format)
        return format

    def get_extension(self, format: str) -> str:
        """
        Gets the file extension for the given format.

        @param format: The image format to get the extension for (e.g., "JPEG").
        
        Returns the file extension corresponding to the format.
        """
        format = self.validate_format(format)
        extension = self.format_extensions[format]
        logger.info("Retrieved file extension for format %s: %s", format, extension)
        return extension


def get_simple_image_validator(format_extensions: Dict[str, str] = Depends(get_format_extensions)) -> SimpleImageValidator:
    """
    Dependency injection function to get a SimpleImageValidator instance.

    @param format_extensions: A dictionary of format extensions, provided by the dependency system.
    
    Returns a SimpleImageValidator instance.
    """
    logger.debug("Creating SimpleImageValidator instance with provided format extensions")
    return SimpleImageValidator(format_extensions=format_extensions)
