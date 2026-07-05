import asyncio
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.validation.validator import validate_upload
from app.vision.service import InferenceService


async def resolve_image_bytes(
    file: UploadFile | None,
    image_name: str | None,
    folder: str,
    service: InferenceService,
) -> tuple[bytes, str]:
    if file is not None:
        await asyncio.to_thread(validate_upload, file)
        content = await file.read()
        return content, file.filename or "image.jpg"

    if image_name is not None:
        image_path = service.image_service.get_image_path(image_name, folder)
        return Path(image_path).read_bytes(), image_name

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Provide a multipart file or image_name query parameter.",
    )
