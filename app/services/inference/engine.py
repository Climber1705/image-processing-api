from dataclasses import dataclass
import warnings

import torch
from PIL import Image
from transformers import DetrForObjectDetection, DetrImageProcessor

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.services.inference.postprocessor import postprocess
from app.services.inference.preprocessor import preprocess
from app.services.inference.schemas import DetectionResult

logger = get_logger("inference_engine")


@dataclass(frozen=True, slots=True)
class EngineMetadata:
    model_name: str
    model_revision: str | None


class InferenceEngine:
    def __init__(
        self,
        processor: DetrImageProcessor,
        model: DetrForObjectDetection,
        metadata: EngineMetadata,
        device: str = "cpu",
        max_image_dimension: int = 1333,
    ) -> None:
        self.processor = processor
        self.model = model
        self.metadata = metadata
        self.device = device
        self.max_image_dimension = max_image_dimension
        self._warmed_up = False
        self._inference_count = 0

        self.model.to(device)
        self.model.eval()

    @classmethod
    def from_settings(cls, settings: Settings) -> "InferenceEngine":
        warnings.filterwarnings("ignore", category=UserWarning, module="torch")

        model_name = settings.MODEL_NAME
        logger.info("Loading detection model: %s", model_name)

        processor = DetrImageProcessor.from_pretrained(
            model_name,
            revision=settings.MODEL_REVISION,
        )
        model = DetrForObjectDetection.from_pretrained(
            model_name,
            revision=settings.MODEL_REVISION,
            ignore_mismatched_sizes=True,
        )

        return cls(
            processor=processor,
            model=model,
            metadata=EngineMetadata(
                model_name=model_name,
                model_revision=settings.MODEL_REVISION,
            ),
            device=settings.INFERENCE_DEVICE,
            max_image_dimension=settings.MAX_IMAGE_DIMENSION,
        )

    def warmup(self) -> None:
        dummy = Image.new("RGB", (64, 64), color=(0, 0, 0))
        inputs = preprocess(dummy, self.processor, self.device)

        with torch.inference_mode():
            self.model(**inputs)

        self._warmed_up = True
        logger.info("Inference engine warmup complete")

    def mark_ready(self) -> None:
        self._warmed_up = True

    def predict(self, image: Image.Image, confidence_threshold: float) -> DetectionResult:
        inputs = preprocess(
            image,
            self.processor,
            self.device,
            max_dimension=self.max_image_dimension,
        )

        with torch.inference_mode():
            outputs = self.model(**inputs)
            self._inference_count += 1

        detections = postprocess(
            outputs,
            self.processor,
            image.size,
            self.model.config.id2label,
            confidence_threshold,
        )

        return DetectionResult(
            detections=detections,
            model_name=self.metadata.model_name,
            model_version=self.metadata.model_revision,
        )

    @property
    def is_ready(self) -> bool:
        return self._warmed_up

    @property
    def inference_count(self) -> int:
        return self._inference_count
