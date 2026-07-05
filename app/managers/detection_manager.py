from typing import Any
from fastapi import HTTPException

from app.core.logging_config import get_logger
from app.services.detection.detection_service import ObjectDetectionService

logger = get_logger("detection_manager")


class DetectionManager:
    def __init__(self, detection_service: ObjectDetectionService):
        self.detection_service = detection_service

    def process_image_for_detection(self, image_path: str) -> dict[str, Any]:
        try:
            logger.info(f"Starting object detection on image: {image_path}")
            result = self.detection_service.detect_with_visualization(image_path)
            logger.info(f"Detection completed for image: {image_path}")
            return result
        except Exception as e:
            logger.error(f"Object detection failed for {image_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")

    def get_detected_objects_summary(self, image_path: str) -> dict[str, Any]:
        try:
            logger.info(f"Fetching detection summary for image: {image_path}")
            detections = self.detection_service.get_detected_objects(image_path)
            engine = self.detection_service.engine
            return {
                "detections": detections,
                "model_name": engine.metadata.model_name,
                "model_version": engine.metadata.model_revision,
            }
        except Exception as e:
            logger.error(f"Detection summary failed for {image_path}: {str(e)}")
            raise RuntimeError(f"Detection summary failed: {str(e)}")
