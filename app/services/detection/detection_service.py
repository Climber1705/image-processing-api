import os
from io import BytesIO
from tempfile import SpooledTemporaryFile

from fastapi import UploadFile
from PIL import Image
from typing import Any

from app.core.config import settings
from app.storage.local_storage import LocalImageStorage
from app.services.inference.engine import InferenceEngine
from app.services.inference.preprocessor import load_image
from app.services.inference.schemas import DetectionResult
from app.services.inference.visualizer import draw_bounding_boxes
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

    def _pillow_to_uploadfile(self, image: Image.Image, filename: str = "image.png") -> UploadFile:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or "PNG")
        img_byte_arr.seek(0)

        temp_file = SpooledTemporaryFile()
        temp_file.write(img_byte_arr.read())
        temp_file.seek(0)

        return UploadFile(filename=filename, file=temp_file)

    def _predict(self, image_path: str) -> tuple[DetectionResult, Image.Image]:
        image = load_image(image_path)
        result = self.engine.predict(image, self.confidence_threshold)
        return result, image

    def detect_with_visualization(self, image_path: str) -> dict[str, Any]:
        result, image = self._predict(image_path)

        annotated = draw_bounding_boxes(image, result.detections)

        original_filename = os.path.basename(image_path)
        name, ext = os.path.splitext(original_filename)
        new_filename = f"{name}_bounding_boxes{ext}"
        save_format = ext.lstrip(".").upper() or "PNG"

        output_path = self.local_storage.save(
            file=self._pillow_to_uploadfile(annotated, filename=new_filename),
            folder="detected",
            filename=new_filename,
            format=save_format,
        )

        logger.info(f"Bounding boxes saved to: {output_path}")
        return {
            "image_with_boxes": output_path,
            "detections": result.to_dict_list(),
            "model_name": result.model_name,
            "model_version": result.model_version,
        }

    def get_bounding_boxes(self, image_path: str) -> str:
        data = self.detect_with_visualization(image_path)
        return data["image_with_boxes"]

    def get_detected_objects(self, image_path: str) -> list[dict]:
        result, _ = self._predict(image_path)
        logger.info(f"Detected {len(result.detections)} objects.")
        return result.to_dict_list()
