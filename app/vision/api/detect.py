from fastapi import UploadFile

from app.dependencies.inference import run_inference
from app.vision.api.inputs import resolve_image_bytes
from app.vision.domain.dtos import DetectResponseDTO
from app.vision.service import InferenceService


async def run_detect(
    file: UploadFile | None,
    image_name: str | None,
    folder: str,
    service: InferenceService,
    visualize: bool,
    persist: bool = False,
) -> DetectResponseDTO:
    image_bytes, source_filename = await resolve_image_bytes(file, image_name, folder, service)
    return await run_inference(
        lambda: service.detect(
            image_bytes,
            visualize=visualize,
            persist=persist,
            source_filename=source_filename,
        ),
    )
