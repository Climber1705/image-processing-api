from pydantic import BaseModel


class DetectionBox(BaseModel):
    label: str
    confidence: float
    box: list[float]


class BoundingBoxResponse(BaseModel):
    message: str
    image_path: str
    detections: list[DetectionBox]
    model_name: str
    model_version: str | None = None


class DetectedObjectsResponse(BaseModel):
    message: str
    detected_objects: list[DetectionBox]
    model_name: str
    model_version: str | None = None
