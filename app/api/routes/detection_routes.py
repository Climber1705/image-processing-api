from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
import asyncio
import time

from app.utils.file_operations.file_utils import FilePathResolver, get_file_path_resolver
from app.managers.detection_manager import DetectionManager, get_detection_manager
from app.schemas.detection.detection_responses import BoundingBoxResponse, DetectedObjectsResponse, DetectionBox
from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger

logger = get_logger("detection_routes")

router = APIRouter(prefix="/images/detect", tags=["Image Detections"])

DetectionManagerDep = Annotated[DetectionManager, Depends(get_detection_manager)]
FilePathResolverDep = Annotated[FilePathResolver, Depends(get_file_path_resolver)]


@router.post("/bounding_boxes/", response_model=BoundingBoxResponse)
@limiter.limit("5/minute")
async def bounding_boxes(
    request: Request,
    image_name: str,
    manager: DetectionManagerDep,
    file_resolver: FilePathResolverDep,
):
    """Run DETR detection and save an annotated image with bounding boxes."""
    start_time = time.time()
    logger.info(f"Request to detect bounding boxes for image: {image_name}")

    image_path = await asyncio.to_thread(file_resolver.find_and_validate_image, image_name)

    try:
        logger.info(f"Processing image for bounding boxes: {image_name}")
        data = await asyncio.to_thread(manager.process_image_for_detection, image_path)
    except RuntimeError as e:
        logger.error(f"Error processing image: {image_name}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

    execution_time = time.time() - start_time
    logger.info(
        f"Successfully detected bounding boxes for image: {image_name}, Execution Time: {execution_time:.2f}s"
    )

    return BoundingBoxResponse(
        message="Bounding boxes drawn successfully",
        image_path=data["image_with_boxes"],
        detections=[DetectionBox(**d) for d in data["detections"]],
        model_name=data["model_name"],
        model_version=data.get("model_version"),
    )


@router.get("/detected_objects/", response_model=DetectedObjectsResponse)
@limiter.limit("10/minute")
async def detected_objects(
    request: Request,
    image_name: str,
    manager: DetectionManagerDep,
    file_resolver: FilePathResolverDep,
):
    """Run DETR detection and return label/confidence/box metadata only."""
    start_time = time.time()
    logger.info(f"Request to retrieve detected objects for image: {image_name}")

    image_path = await asyncio.to_thread(file_resolver.find_and_validate_image, image_name)

    try:
        logger.info(f"Retrieving detected objects for image: {image_name}")
        summary = await asyncio.to_thread(manager.get_detected_objects_summary, image_path)
    except RuntimeError as e:
        logger.error(f"Error retrieving detected objects for image: {image_name}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving detected objects: {str(e)}")

    execution_time = time.time() - start_time
    logger.info(
        f"Successfully retrieved detected objects for image: {image_name}, Execution Time: {execution_time:.2f}s"
    )

    return DetectedObjectsResponse(
        message="Detected objects retrieved successfully",
        detected_objects=[DetectionBox(**d) for d in summary["detections"]],
        model_name=summary["model_name"],
        model_version=summary.get("model_version"),
    )
