from pydantic import BaseModel, Field


class DetectionBox(BaseModel):
    label: str
    confidence: float
    box: list[float]


class InferenceMetadata(BaseModel):
    model_name: str
    model_version: str | None = None


class InferenceDetectResponse(BaseModel):
    message: str
    detections: list[DetectionBox]
    model_name: str
    model_version: str | None = None
    detection_count: int = Field(..., ge=0)


class InferenceDetectVisualizeResponse(InferenceDetectResponse):
    image_path: str | None = None
    annotated_image_base64: str | None = None


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str | None = None
    is_ready: bool
    inference_count: int = Field(..., ge=0)
