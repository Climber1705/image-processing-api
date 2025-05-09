from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Annotated
from app.utils.file_operations.file_utils import FilePathResolver, get_file_path_resolver
from app.managers.detection_manager import DetectionManager, get_detection_manager
from app.schemas.detection.detection_responses import BoundingBoxResponse, DetectedObjectsResponse, DetectionBox
from app.core.rate_limiting import limiter
from app.core.logging_config import get_logger
import time

# Setting up a logger for this module
logger = get_logger("detection_routes")

# Define the router with prefix and tags for better organization in FastAPI
router = APIRouter(prefix="/images/detect", tags=["Image Detections"])

# Dependency injections for DetectionManager and FilePathResolver
DetectionManagerDep = Annotated[DetectionManager, Depends(get_detection_manager)]
FilePathResolverDep = Annotated[FilePathResolver, Depends(get_file_path_resolver)]

# POST endpoint for detecting bounding boxes in an image
@router.post("/bounding_boxes/", response_model=BoundingBoxResponse)
@limiter.limit("5/minute")  # Rate limiting: 5 requests per minute
async def bounding_boxes(
    request: Request,
    image_name: str,
    manager: DetectionManagerDep,
    file_resolver: FilePathResolverDep,
):
    """
    Detects bounding boxes in the specified image.

    - **Parameters:**
        - **image_name**: The name of the image for which bounding boxes are to be detected.

    - **Returns:**
        - A **BoundingBoxResponse** containing:
            - **message**: A success message.
            - **image_path**: The processed image with bounding boxes drawn.
            - **detections**: A list of detected bounding boxes as **DetectionBox** objects.
    """
    start_time = time.time()  # Start tracking execution time
    logger.info(f"Request to detect bounding boxes for image: {image_name}")

    # Check if the image exists
    image_path = file_resolver.find_and_validate_image(image_name)

    try:
        # Process the image to detect bounding boxes
        logger.info(f"Processing image for bounding boxes: {image_name}")
        data = manager.process_image_for_detection(image_path)
    except RuntimeError as e:
        logger.error(f"Error processing image: {image_name}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

    execution_time = time.time() - start_time
    logger.info(f"Successfully detected bounding boxes for image: {image_name}, Execution Time: {execution_time:.2f}s")
    
    return BoundingBoxResponse(
        message="Bounding boxes drawn successfully",
        image_path=data["image_with_boxes"],
        detections=[DetectionBox(**d) for d in data["detections"]]
    )


# GET endpoint for retrieving detected objects from an image
@router.get("/detected_objects/", response_model=DetectedObjectsResponse)
@limiter.limit("10/minute")  # Rate limiting: 10 requests per minute
async def detected_objects(
    request: Request,
    image_name: str,
    manager: DetectionManagerDep,
    file_resolver: FilePathResolverDep,
):
    """
    Retrieves the list of detected objects from the specified image.

    - **Parameters:**
        - **image_name**: The name of the image from which detected objects will be retrieved.

    - **Returns:**
        - A **DetectedObjectsResponse** containing:
            - **message**: A success message.
            - **detected_objects**: A list of detected objects with their metadata.
    """
    start_time = time.time()  # Start tracking execution time
    logger.info(f"Request to retrieve detected objects for image: {image_name}")

    # Check if the image exists
    image_path = file_resolver.find_and_validate_image(image_name)

    try:
        logger.info(f"Retrieving detected objects for image: {image_name}")
        detected = manager.get_detected_objects_summary(image_path)
    except RuntimeError as e:
        logger.error(f"Error retrieving detected objects for image: {image_name}, Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving detected objects: {str(e)}")

    execution_time = time.time() - start_time
    logger.info(f"Successfully retrieved detected objects for image: {image_name}, Execution Time: {execution_time:.2f}s")

    return DetectedObjectsResponse(
        message="Detected objects retrieved successfully",
        detected_objects=detected
    )
