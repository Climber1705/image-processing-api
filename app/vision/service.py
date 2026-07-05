from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import settings
from app.core.logging_config import get_logger
from app.media.domain.enums import ImageFolder
from app.media.domain.errors import ImageNotFoundError
from app.media.repository import ImageRepository
from app.media.service import ImageService
from app.storage.base_storage import BaseImageStorage
from app.vision.domain.dtos import DetectionsResultDTO, DetectResponseDTO
from app.vision.domain.errors import (
    CorruptImageError,
    InferenceError,
    ModelNotReadyError,
)
from app.vision.inference.engine import InferenceEngine
from app.vision.inference.mappers import to_detect_response_dto, to_detections_result_dto
from app.vision.inference.schemas import DetectionResult
from app.vision.inference.visualizer import draw_bounding_boxes

logger = get_logger("inference_service")


class InferenceService:
    def __init__(
        self,
        engine: InferenceEngine,
        storage: BaseImageStorage,
        image_service: ImageService,
        image_repository: ImageRepository,
        confidence_threshold: float | None = None,
    ) -> None:
        self.engine = engine
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )
        self.storage = storage
        self.image_service = image_service
        self.image_repository = image_repository

    def _ensure_ready(self) -> None:
        if not self.engine.is_ready:
            raise ModelNotReadyError("Inference engine is not ready")

    def _load_and_validate_image(self, image_path: str) -> Image.Image:
        path = Path(image_path)
        if not path.exists():
            raise ImageNotFoundError(f"Image {path.name} not found")

        if path.stat().st_size == 0:
            raise CorruptImageError(f"Image file is empty: {path.name}")

        try:
            with Image.open(path) as img:
                img.verify()
        except (UnidentifiedImageError, OSError, SyntaxError) as exc:
            raise CorruptImageError(f"Image file is corrupt or unreadable: {path.name}") from exc

        try:
            with Image.open(path) as img:
                if img.width <= 0 or img.height <= 0:
                    raise CorruptImageError(f"Image has invalid dimensions: {path.name}")
                return img.convert("RGB")
        except CorruptImageError:
            raise
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise CorruptImageError(f"Image file is corrupt or unreadable: {path.name}") from exc

    def _run_inference(self, image_path: str) -> tuple[DetectionResult, Image.Image]:
        self._ensure_ready()
        image = self._load_and_validate_image(image_path)
        try:
            result = self.engine.predict(image, self.confidence_threshold)
        except Exception as exc:
            logger.error("Inference failed for %s: %s", image_path, exc)
            raise InferenceError(f"Inference failed: {exc}") from exc
        return result, image

    def _image_to_bytesio(self, image: Image.Image) -> BytesIO:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or "PNG")
        img_byte_arr.seek(0)
        return img_byte_arr

    def _persist_annotation(self, annotated: Image.Image, source_filename: str) -> str:
        source_stem = Path(source_filename).stem
        source_ext = Path(source_filename).suffix or ".jpg"
        display_filename = f"{source_stem}_bounding_boxes{source_ext}"
        save_format = source_ext.lstrip(".").upper() or "PNG"
        storage_id = self.image_repository.get_or_create_image_id(
            display_filename,
            ImageFolder.DETECTED,
        )

        output_path = self.storage.save(
            file=self._image_to_bytesio(annotated),
            folder=ImageFolder.DETECTED,
            storage_id=storage_id,
            format=save_format,
        )
        self.image_repository.upsert_record(
            path=output_path,
            folder=ImageFolder.DETECTED,
            display_filename=display_filename,
            image_id=storage_id,
        )
        return output_path

    def detect_for_filename(self, filename: str, folder: str = ImageFolder.UPLOADED) -> DetectResponseDTO:
        image_path = str(self.image_service.get_image_path(filename, folder))
        return self.detect_with_visualization(image_path, filename)

    def get_detected_objects_for_filename(
        self,
        filename: str,
        folder: str = ImageFolder.UPLOADED,
    ) -> DetectionsResultDTO:
        image_path = str(self.image_service.get_image_path(filename, folder))
        return self.get_detected_objects(image_path)

    def detect_with_visualization(self, image_path: str, source_filename: str) -> DetectResponseDTO:
        result, image = self._run_inference(image_path)
        annotated = draw_bounding_boxes(image, result.detections)
        output_path = self._persist_annotation(annotated, source_filename)
        return to_detect_response_dto(result, output_path)

    def get_detected_objects(self, image_path: str) -> DetectionsResultDTO:
        result, _ = self._run_inference(image_path)
        return to_detections_result_dto(result)
