from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DetectionDTO:
    label: str
    confidence: float
    box: list[float]


@dataclass(frozen=True, slots=True)
class InferenceMetadataDTO:
    model_name: str
    model_version: str | None


@dataclass(frozen=True, slots=True)
class DetectionsResultDTO:
    detections: list[DetectionDTO]
    metadata: InferenceMetadataDTO


@dataclass(frozen=True, slots=True)
class DetectResponseDTO(DetectionsResultDTO):
    image_path: str
