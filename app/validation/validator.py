import io
import logging

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger("validator")

DEFAULT_MAX_SIZE_MB = 5

# MIME types aligned with Settings.FORMAT_EXTENSIONS (app/core/config.py).
FORMAT_TO_MIME: dict[str, str] = {
    "JPEG": "image/jpeg",
    "JPG": "image/jpeg",
    "PNG": "image/png",
    "GIF": "image/gif",
    "BMP": "image/bmp",
    "TIFF": "image/tiff",
    "WEBP": "image/webp",
}


def allowed_mime_types_for_formats(format_extensions: dict[str, str]) -> tuple[str, ...]:
    mimes = {
        FORMAT_TO_MIME[fmt]
        for fmt in format_extensions
        if fmt in FORMAT_TO_MIME
    }
    return tuple(sorted(mimes))


def default_allowed_mime_types() -> tuple[str, ...]:
    from app.core.config import get_settings

    return allowed_mime_types_for_formats(get_settings().format_extensions)


def validate_image_type(
    image: UploadFile,
    allowed_types: tuple[str, ...] | None = None,
) -> None:
    if allowed_types is None:
        allowed_types = default_allowed_mime_types()
    if image.content_type not in allowed_types:
        logger.warning("Unsupported file type: %s", image.content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type.",
        )


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


def validate_upload(
    image: UploadFile,
    allowed_types: tuple[str, ...] | None = None,
    max_size_mb: int = DEFAULT_MAX_SIZE_MB,
) -> None:
    validate_image_type(image, allowed_types)
    validate_image_size(image, max_size_mb * 1024 * 1024)


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
    return format


def get_format_extension(format: str, format_extensions: dict[str, str]) -> str:
    format = validate_image_format(format, format_extensions)
    return format_extensions[format]
