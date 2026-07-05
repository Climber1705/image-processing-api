from pydantic import BaseModel, Field


class DetectionBox(BaseModel):
    label: str
    confidence: float
    box: list[float]


class InferenceMetadata(BaseModel):
    model_name: str
    model_version: str | None = None


class BoundingBoxResponse(BaseModel):
    message: str
    image_path: str
    detections: list[DetectionBox]
    model_name: str
    model_version: str | None = None
    detection_count: int = Field(..., ge=0)


class DetectedObjectsResponse(BaseModel):
    message: str
    detected_objects: list[DetectionBox]
    model_name: str
    model_version: str | None = None
    detection_count: int = Field(..., ge=0)
