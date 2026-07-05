import os
from io import BytesIO
from fastapi import HTTPException
from PIL import Image
from typing import Any

from app.core.config import settings
from app.storage.local_storage import LocalImageStorage
from app.vision.inference.engine import InferenceEngine
from app.vision.inference.preprocessor import load_image
from app.vision.inference.schemas import DetectionResult
from app.vision.inference.visualizer import draw_bounding_boxes
from app.core.logging_config import get_logger


logger = get_logger("detection_service")


class ObjectDetectionService:
    def __init__(
        self,
        inference_engine: InferenceEngine,
        local_storage: LocalImageStorage,
        confidence_threshold: float | None = None,
    ) -> None:
        self.engine = inference_engine
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.local_storage = local_storage

    @property
    def processor(self):
        return self.engine.processor

    @property
    def model(self):
        return self.engine.model

    def _image_to_bytesio(self, image: Image.Image) -> BytesIO:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or "PNG")
        img_byte_arr.seek(0)
        return img_byte_arr

    def _predict(self, image_path: str) -> tuple[DetectionResult, Image.Image]:
        image = load_image(image_path)
        result = self.engine.predict(image, self.confidence_threshold)
        return result, image

    def detect_with_visualization(self, image_path: str) -> dict[str, Any]:
        try:
            logger.info(f"Starting object detection on image: {image_path}")
            result, image = self._predict(image_path)

            annotated = draw_bounding_boxes(image, result.detections)

            original_filename = os.path.basename(image_path)
            name, ext = os.path.splitext(original_filename)
            new_filename = f"{name}_bounding_boxes{ext}"
            save_format = ext.lstrip(".").upper() or "PNG"

            output_path = self.local_storage.save(
                file=self._image_to_bytesio(annotated),
                folder="detected",
                filename=new_filename,
                format=save_format,
            )

            logger.info(f"Bounding boxes saved to: {output_path}")
            logger.info(f"Detection completed for image: {image_path}")
            return {
                "image_with_boxes": output_path,
                "detections": result.to_dict_list(),
                "model_name": result.model_name,
                "model_version": result.model_version,
            }
        except Exception as e:
            logger.error(f"Object detection failed for {image_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Object detection failed: {str(e)}")

    def get_bounding_boxes(self, image_path: str) -> str:
        data = self.detect_with_visualization(image_path)
        return data["image_with_boxes"]

    def get_detected_objects(self, image_path: str) -> dict[str, Any]:
        try:
            result, _ = self._predict(image_path)
            logger.info(f"Detected {len(result.detections)} objects.")
            return {
                "detections": result.to_dict_list(),
                "model_name": result.model_name,
                "model_version": result.model_version,
            }
        except Exception as e:
            logger.error(f"Detection summary failed for {image_path}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Detection summary failed: {str(e)}")
