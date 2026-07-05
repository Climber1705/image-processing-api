from pydantic import BaseModel
from typing import List


class DetectionBox(BaseModel):
    label: str
    confidence: float
    box: List[float]


class BoundingBoxResponse(BaseModel):
    message: str
    image_path: str
    detections: List[DetectionBox]


class DetectedObjectsResponse(BaseModel):
    message: str
    detected_objects: List[DetectionBox]
