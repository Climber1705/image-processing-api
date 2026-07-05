from io import BytesIO
from pathlib import Path
from fastapi import HTTPException
from PIL import Image
from typing import Any

from app.core.config import settings
from app.storage.base_storage import BaseImageStorage
from app.media.repository import ImageRepository
from app.media.service import ImageService
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
        storage: BaseImageStorage,
        image_service: ImageService,
        image_repository: ImageRepository,
        confidence_threshold: float | None = None,
    ) -> None:
        self.engine = inference_engine
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.storage = storage
        self.image_service = image_service
        self.image_repository = image_repository

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

    def detect_for_filename(self, filename: str, folder: str = "uploaded") -> dict[str, Any]:
        image_path = str(self.image_service.get_image_path(filename, folder))
        return self.detect_with_visualization(image_path, filename)

    def get_detected_objects_for_filename(self, filename: str, folder: str = "uploaded") -> dict[str, Any]:
        image_path = str(self.image_service.get_image_path(filename, folder))
        return self.get_detected_objects(image_path)

    def detect_with_visualization(self, image_path: str, source_filename: str) -> dict[str, Any]:
        try:
            logger.info(f"Starting object detection on image: {image_path}")
            result, image = self._predict(image_path)

            annotated = draw_bounding_boxes(image, result.detections)

            source_stem = Path(source_filename).stem
            source_ext = Path(source_filename).suffix or ".jpg"
            display_filename = f"{source_stem}_bounding_boxes{source_ext}"
            save_format = source_ext.lstrip(".").upper() or "PNG"
            storage_id = self.image_repository.get_or_create_image_id(display_filename, "detected")

            output_path = self.storage.save(
                file=self._image_to_bytesio(annotated),
                folder="detected",
                storage_id=storage_id,
                format=save_format,
            )
            self.image_repository.upsert_record(
                path=output_path,
                folder="detected",
                display_filename=display_filename,
                image_id=storage_id,
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

    def get_bounding_boxes(self, image_path: str, source_filename: str) -> str:
        data = self.detect_with_visualization(image_path, source_filename)
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
