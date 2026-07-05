from dataclasses import dataclass

from app.vision.domain.dtos import DetectionDTO


@dataclass(frozen=True, slots=True)
class DetectionResult:
    detections: list[DetectionDTO]
    model_name: str
    model_version: str | None


@dataclass(frozen=True, slots=True)
class EngineMetadata:
    model_name: str
    model_revision: str | None
