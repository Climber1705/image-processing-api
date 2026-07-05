from dataclasses import dataclass
import warnings

import torch
from PIL import Image
from transformers import DetrForObjectDetection, DetrImageProcessor

from app.core.config import Settings
from app.core.logging_config import get_logger

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
    ) -> None:
        self.processor = processor
        self.model = model
        self.metadata = metadata
        self.device = device
        self._warmed_up = False

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
        )

    def warmup(self) -> None:
        dummy = Image.new("RGB", (64, 64), color=(0, 0, 0))
        inputs = self.processor(images=dummy, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}

        with torch.inference_mode():
            self.model(**inputs)

        self._warmed_up = True
        logger.info("Inference engine warmup complete")

    @property
    def is_ready(self) -> bool:
        return self._warmed_up
