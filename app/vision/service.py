import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.core.config import settings
from app.core.logging_config import get_logger
from app.media.domain.enums import ImageFolder
from app.media.repository import ImageRepository
from app.media.service import ImageService
from app.media.utils.filename import build_display_filename
from app.storage.base_storage import BaseImageStorage
from app.vision.domain.dtos import DetectResponseDTO
from app.vision.domain.errors import InferenceError, ModelNotReadyError
from app.vision.image_loader import load_from_bytes, load_from_path
from app.vision.inference.engine import InferenceEngine
from app.vision.inference.mappers import to_detect_response_dto
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

    def _predict(self, image: Image.Image, source_label: str = "image") -> DetectionResult:
        self._ensure_ready()
        try:
            return self.engine.predict(image, self.confidence_threshold)
        except Exception as exc:
            logger.error("Inference failed for %s: %s", source_label, exc)
            raise InferenceError(f"Inference failed: {exc}") from exc

    def _image_to_bytesio(self, image: Image.Image) -> BytesIO:
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format=image.format or "PNG")
        img_byte_arr.seek(0)
        return img_byte_arr

    def _encode_image_base64(self, image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format=image.format or "PNG")
        return base64.b64encode(buffer.getvalue()).decode("ascii")

    def _persist_annotation(self, annotated: Image.Image, source_filename: str) -> str:
        display_filename = build_display_filename(source_filename, suffix="bounding_boxes")
        save_format = Path(display_filename).suffix.lstrip(".").upper() or "PNG"
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
        self.image_repository.upsert(
            path=output_path,
            folder=ImageFolder.DETECTED,
            display_filename=display_filename,
            image_id=storage_id,
        )
        return output_path

    def detect(
        self,
        image: bytes,
        visualize: bool = False,
        persist: bool = False,
        source_filename: str = "image.jpg",
    ) -> DetectResponseDTO:
        pil = load_from_bytes(image, source_filename)
        return self._run_detection(pil, visualize, persist, source_filename)

    def detect_from_path(
        self,
        image_path: str,
        visualize: bool = False,
        persist: bool = False,
        source_filename: str | None = None,
    ) -> DetectResponseDTO:
        pil = load_from_path(Path(image_path))
        filename = source_filename or Path(image_path).name
        return self._run_detection(pil, visualize, persist, filename)

    def _run_detection(
        self,
        image: Image.Image,
        visualize: bool,
        persist: bool,
        source_filename: str,
    ) -> DetectResponseDTO:
        result = self._predict(image, source_label=source_filename)

        if not visualize:
            return to_detect_response_dto(result)

        annotated = draw_bounding_boxes(image, result.detections)
        image_path = self._persist_annotation(annotated, source_filename) if persist else None
        encoded = None if persist else self._encode_image_base64(annotated)

        return to_detect_response_dto(
            result,
            image_path=image_path,
            annotated_image_base64=encoded,
        )
