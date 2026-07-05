from fastapi import APIRouter, Depends, File, Query, Request, UploadFile

from app.core.rate_limiting import limiter
from app.dependencies.inference import run_inference
from app.dependencies.services import get_inference_service
from app.vision.api import InferenceDetectResponse, InferenceDetectVisualizeResponse, ModelInfoResponse
from app.vision.api.inputs import resolve_image_bytes
from app.vision.api.mappers import (
    from_engine_metadata,
    to_inference_detect_response,
    to_inference_visualize_response,
)
from app.vision.inference.engine import InferenceEngine
from app.vision.service import InferenceService

router = APIRouter(prefix="/v1/inference", tags=["Inference"])


@router.post("/detect", response_model=InferenceDetectResponse)
@limiter.limit("10/minute")
async def detect(
    request: Request,
    file: UploadFile | None = File(None),
    image_name: str | None = Query(None, description="Reference an existing stored image by name."),
    folder: str = Query("uploaded", description="Folder for image_name lookup (defaults to 'uploaded')."),
    service: InferenceService = Depends(get_inference_service),
):
    """Run object detection on an uploaded image or a stored image by reference."""
    image_bytes, source_filename = await resolve_image_bytes(file, image_name, folder, service)
    result = await run_inference(
        lambda: service.detect(image_bytes, source_filename=source_filename),
    )
    return to_inference_detect_response(result)


@router.post("/detect/visualize", response_model=InferenceDetectVisualizeResponse)
@limiter.limit("5/minute")
async def detect_with_visualization(
    request: Request,
    file: UploadFile | None = File(None),
    image_name: str | None = Query(None, description="Reference an existing stored image by name."),
    folder: str = Query("uploaded", description="Folder for image_name lookup (defaults to 'uploaded')."),
    persist: bool = Query(False, description="Save annotated image to storage when true."),
    service: InferenceService = Depends(get_inference_service),
):
    """Run object detection and return bounding-box visualization."""
    image_bytes, source_filename = await resolve_image_bytes(file, image_name, folder, service)
    result = await run_inference(
        lambda: service.detect(
            image_bytes,
            visualize=True,
            persist=persist,
            source_filename=source_filename,
        ),
    )
    return to_inference_visualize_response(result)


@router.get("/models", response_model=ModelInfoResponse)
@limiter.limit("30/minute")
async def list_models(request: Request):
    """Return metadata for the loaded inference model."""
    engine: InferenceEngine = request.app.state.inference_engine
    return from_engine_metadata(engine)
