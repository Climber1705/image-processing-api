import asyncio
from fastapi import APIRouter, Depends, Query, Request

from app.core.rate_limiting import limiter
from app.dependencies.services import get_inference_service
from app.vision.api import BoundingBoxResponse, DetectedObjectsResponse
from app.vision.api.mappers import to_bounding_box_response, to_detected_objects_response
from app.vision.service import InferenceService

router = APIRouter(prefix="/images/{filename}/detections", tags=["Image Detections"])


@router.post("/bounding-boxes", response_model=BoundingBoxResponse)
@limiter.limit("5/minute")
async def create_detection_with_visualization(
    request: Request,
    filename: str,
    service: InferenceService = Depends(get_inference_service),
    folder: str = Query("uploaded", description="The folder containing the image (defaults to 'uploaded')."),
):
    """Run DETR detection and save an annotated image with bounding boxes."""
    result = await asyncio.to_thread(
        service.detect_for_filename,
        filename,
        folder,
    )
    return to_bounding_box_response(result)


@router.get("", response_model=DetectedObjectsResponse)
@limiter.limit("10/minute")
async def list_detections(
    request: Request,
    filename: str,
    service: InferenceService = Depends(get_inference_service),
    folder: str = Query("uploaded", description="The folder containing the image (defaults to 'uploaded')."),
):
    """Run DETR detection and return label/confidence/box metadata only."""
    result = await asyncio.to_thread(
        service.get_detected_objects_for_filename,
        filename,
        folder,
    )
    return to_detected_objects_response(result)
