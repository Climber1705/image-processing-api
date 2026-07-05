import asyncio
from fastapi import APIRouter, Depends, Query, Request

from app.core.rate_limiting import limiter
from app.dependencies.services import get_object_detection_service
from app.vision.detection_service import ObjectDetectionService
from app.vision.schema import BoundingBoxResponse, DetectedObjectsResponse, DetectionBox

router = APIRouter(prefix="/images/{filename}/detections", tags=["Image Detections"])


@router.post("/bounding-boxes", response_model=BoundingBoxResponse)
@limiter.limit("5/minute")
async def create_detection_with_visualization(
    request: Request,
    filename: str,
    service: ObjectDetectionService = Depends(get_object_detection_service),
    folder: str = Query("uploaded", description="The folder containing the image (defaults to 'uploaded')."),
):
    """Run DETR detection and save an annotated image with bounding boxes."""
    data = await asyncio.to_thread(service.detect_for_filename, filename, folder)

    return BoundingBoxResponse(
        message="Bounding boxes drawn successfully",
        image_path=data["image_with_boxes"],
        detections=[DetectionBox(**d) for d in data["detections"]],
        model_name=data["model_name"],
        model_version=data.get("model_version"),
    )


@router.get("", response_model=DetectedObjectsResponse)
@limiter.limit("10/minute")
async def list_detections(
    request: Request,
    filename: str,
    service: ObjectDetectionService = Depends(get_object_detection_service),
    folder: str = Query("uploaded", description="The folder containing the image (defaults to 'uploaded')."),
):
    """Run DETR detection and return label/confidence/box metadata only."""
    summary = await asyncio.to_thread(service.get_detected_objects_for_filename, filename, folder)

    return DetectedObjectsResponse(
        message="Detected objects retrieved successfully",
        detected_objects=[DetectionBox(**d) for d in summary["detections"]],
        model_name=summary["model_name"],
        model_version=summary.get("model_version"),
    )
