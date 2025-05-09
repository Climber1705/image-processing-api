from fastapi import Depends, HTTPException
from typing import List, Annotated

from app.services.detection.detection_service import ObjectDetectionService, get_object_detection_service
from app.core.logging_config import get_logger

# Initialize logger for detection
logger = get_logger("detection_manager")

# Annotated dependency for Object Detection
ObjectDetectionServiceDep = Annotated[ObjectDetectionService, Depends(get_object_detection_service)]

class DetectionManager:
    """
    Handles image processing tasks related to object detection by delegating
    to the ObjectDetectionService.

    @param detection_service: Instance of ObjectDetectionService providing object detection functionalities.
    """
    def __init__(self, detection_service: ObjectDetectionServiceDep):
        self.detection_service = detection_service

    def process_image_for_detection(self, image_path: str) -> dict:
        """
        Processes an image to generate bounding boxes and detect objects.
        
        @param image_path: Path to the image file.
        @return: Dict with path to output image and list of detected objects.
        """
        try:
            logger.info(f"Starting object detection on image: {image_path}")
            output_image_path = self.detection_service.get_bounding_boxes(image_path)
            detected_objects = self.detection_service.get_detected_objects(image_path)
            logger.info(f"Detection completed for image: {image_path}")
            return {
                "image_with_boxes": output_image_path,
                "detections": detected_objects
            }
        except Exception as e:
            logger.error(f"Object detection failed for {image_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")

    def get_detected_objects_summary(self, image_path: str) -> List[dict]:
        """
        Retrieves only the list of detected objects from an image.
        
        @param image_path: Path to the image file.
        @return: List of detected objects.
        """
        try:
            logger.info(f"Fetching detection summary for image: {image_path}")
            return self.detection_service.get_detected_objects(image_path)
        except Exception as e:
            logger.error(f"Detection summary failed for {image_path}: {str(e)}")
            raise RuntimeError(f"Detection summary failed: {str(e)}")

def get_detection_manager(detection_service: ObjectDetectionServiceDep) -> DetectionManager:
    """
    Dependency injector for DetectionManager.

    @param edit_service: Instance of ObjectDetectionService to use.
    @return: Instance of DetectionManager.
    """
    return DetectionManager(detection_service=detection_service)
