import io
import logging

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger("validator")

DEFAULT_ALLOWED_TYPES = ("image/jpeg", "image/png")
DEFAULT_MAX_SIZE_MB = 5


def validate_image_type(
    image: UploadFile,
    allowed_types: tuple[str, ...] = DEFAULT_ALLOWED_TYPES,
) -> None:
    if image.content_type not in allowed_types:
        logger.warning("Unsupported file type: %s", image.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type.",
        )
    logger.info("Validated image type: %s", image.content_type)


def validate_image_size(
    image: UploadFile,
    max_size_bytes: int,
) -> None:
    current_position = image.file.tell()
    image.file.seek(0, io.SEEK_END)
    file_size = image.file.tell()
    image.file.seek(current_position)

    if file_size > max_size_bytes:
        logger.warning(
            "File size too large: %d bytes, max allowed: %d bytes",
            file_size,
            max_size_bytes,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Max size is {} MB.".format(
                max_size_bytes // (1024 * 1024)
            ),
        )
    logger.info("Validated image size: %d bytes", file_size)


def validate_upload(
    image: UploadFile,
    *,
    allowed_types: tuple[str, ...] = DEFAULT_ALLOWED_TYPES,
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
) -> None:
    try:
        logger.debug("Validating image with content type: %s", image.content_type)
        validate_image_type(image, allowed_types)
        validate_image_size(image, max_size_mb * 1024 * 1024)
    except HTTPException as e:
        logger.error("Validation failed: %s", e.detail)
        raise


def validate_image_format(format: str, format_extensions: dict[str, str]) -> str:
    format = format.upper()
    if format not in format_extensions:
        supported_formats = ", ".join(format_extensions.keys())
        logger.warning(
            "Unsupported format: %s. Supported formats: %s",
            format,
            supported_formats,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported image format: {format}. "
                f"Supported formats: {supported_formats}"
            ),
        )
    logger.info("Validated image format: %s", format)
    return format


def get_format_extension(format: str, format_extensions: dict[str, str]) -> str:
    format = validate_image_format(format, format_extensions)
    extension = format_extensions[format]
    logger.info(
        "Retrieved file extension for format %s: %s",
        format,
        extension,
    )
    return extension
