import base64
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
from app.vision.domain.dtos import DetectResponseDTO
from app.vision.domain.errors import (
    CorruptImageError,
    InferenceError,
    ModelNotReadyError,
)
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

    def _load_and_validate_from_bytes(self, data: bytes, label: str) -> Image.Image:
        if not data:
            raise CorruptImageError(f"Image file is empty: {label}")

        try:
            with Image.open(BytesIO(data)) as img:
                img.verify()
        except (UnidentifiedImageError, OSError, SyntaxError) as exc:
            raise CorruptImageError(f"Image file is corrupt or unreadable: {label}") from exc

        try:
            with Image.open(BytesIO(data)) as img:
                if img.width <= 0 or img.height <= 0:
                    raise CorruptImageError(f"Image has invalid dimensions: {label}")
                return img.convert("RGB")
        except CorruptImageError:
            raise
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise CorruptImageError(f"Image file is corrupt or unreadable: {label}") from exc

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

    def detect(
        self,
        image: bytes,
        *,
        visualize: bool = False,
        persist: bool = False,
        source_filename: str = "image.jpg",
    ) -> DetectResponseDTO:
        pil = self._load_and_validate_from_bytes(image, source_filename)
        return self.detect_from_image(
            pil,
            visualize=visualize,
            persist=persist,
            source_filename=source_filename,
        )

    def detect_from_path(
        self,
        image_path: str,
        *,
        visualize: bool = False,
        persist: bool = False,
        source_filename: str | None = None,
    ) -> DetectResponseDTO:
        pil = self._load_and_validate_image(image_path)
        filename = source_filename or Path(image_path).name
        return self.detect_from_image(
            pil,
            visualize=visualize,
            persist=persist,
            source_filename=filename,
        )

    def detect_from_image(
        self,
        image: Image.Image,
        visualize: bool = False,
        persist: bool = False,
        source_filename: str = "image.jpg",
    ) -> DetectResponseDTO:
        result = self._predict(image, source_label=source_filename)

        if not visualize:
            return to_detect_response_dto(result)

        annotated = draw_bounding_boxes(image, result.detections)
        image_path: str | None = None
        annotated_image_base64: str | None = None

        if persist:
            image_path = self._persist_annotation(annotated, source_filename)
        else:
            annotated_image_base64 = self._encode_image_base64(annotated)

        return to_detect_response_dto(
            result,
            image_path=image_path,
            annotated_image_base64=annotated_image_base64,
        )
