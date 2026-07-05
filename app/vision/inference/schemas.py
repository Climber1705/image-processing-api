from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Detection:
    label: str
    confidence: float
    box: list[float]

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": self.confidence,
            "box": self.box,
        }


@dataclass(frozen=True, slots=True)
class DetectionResult:
    detections: list[Detection]
    model_name: str
    model_version: str | None

    def to_dict_list(self) -> list[dict]:
        return [d.to_dict() for d in self.detections]
