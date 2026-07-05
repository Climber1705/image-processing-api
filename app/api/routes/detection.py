import time
import asyncio
from fastapi import APIRouter, Depends, Request

from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger
from app.dependencies.utils import get_file_path_resolver
from app.dependencies.services import get_object_detection_service
from app.vision.detection_service import ObjectDetectionService
from app.media.utils.file_utils import FilePathResolver
from app.vision.schema import BoundingBoxResponse, DetectedObjectsResponse, DetectionBox

logger = get_logger("detection_routes")

router = APIRouter(prefix="/images/{filename}/detections", tags=["Image Detections"])


@router.post("/bounding-boxes", response_model=BoundingBoxResponse)
@limiter.limit("5/minute")
async def create_detection_with_visualization(
    request: Request,
    filename: str,
    service: ObjectDetectionService = Depends(get_object_detection_service),
    file_resolver: FilePathResolver = Depends(get_file_path_resolver),
):
    """Run DETR detection and save an annotated image with bounding boxes."""
    start_time = time.time()
    logger.info(f"Request to detect bounding boxes for image: {filename}")

    image_path = await asyncio.to_thread(file_resolver.find_and_validate_image, filename)

    logger.info(f"Processing image for bounding boxes: {filename}")
    data = await asyncio.to_thread(service.detect_with_visualization, image_path, filename)

    execution_time = time.time() - start_time
    logger.info(
        f"Successfully detected bounding boxes for image: {filename}, Execution Time: {execution_time:.2f}s"
    )

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
    file_resolver: FilePathResolver = Depends(get_file_path_resolver),
):
    """Run DETR detection and return label/confidence/box metadata only."""
    start_time = time.time()
    logger.info(f"Request to retrieve detected objects for image: {filename}")

    image_path = await asyncio.to_thread(file_resolver.find_and_validate_image, filename)

    logger.info(f"Retrieving detected objects for image: {filename}")
    summary = await asyncio.to_thread(service.get_detected_objects, image_path)

    execution_time = time.time() - start_time
    logger.info(
        f"Successfully retrieved detected objects for image: {filename}, Execution Time: {execution_time:.2f}s"
    )

    return DetectedObjectsResponse(
        message="Detected objects retrieved successfully",
        detected_objects=[DetectionBox(**d) for d in summary["detections"]],
        model_name=summary["model_name"],
        model_version=summary.get("model_version"),
    )
