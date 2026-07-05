from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Detection:
    label: str
    confidence: float
    box: list[float]


@dataclass(frozen=True, slots=True)
class DetectionResult:
    detections: list[Detection]
    model_name: str
    model_version: str | None


@dataclass(frozen=True, slots=True)
class EngineMetadata:
    model_name: str
    model_revision: str | None
