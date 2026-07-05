from app.vision.api.responses import (
    DetectionBox,
    InferenceDetectResponse,
    InferenceDetectVisualizeResponse,
    ModelInfoResponse,
)
from app.vision.domain.dtos import DetectResponseDTO
from app.vision.inference.engine import InferenceEngine


def _to_detection_boxes(detections) -> list[DetectionBox]:
    return [
        DetectionBox(label=d.label, confidence=d.confidence, box=d.box)
        for d in detections
    ]


def to_inference_detect_response(result: DetectResponseDTO) -> InferenceDetectResponse:
    return InferenceDetectResponse(
        message="Detection completed successfully",
        detections=_to_detection_boxes(result.detections),
        model_name=result.metadata.model_name,
        model_version=result.metadata.model_version,
        detection_count=len(result.detections),
    )


def to_inference_visualize_response(
    result: DetectResponseDTO,
) -> InferenceDetectVisualizeResponse:
    return InferenceDetectVisualizeResponse(
        message="Detection with visualization completed successfully",
        detections=_to_detection_boxes(result.detections),
        model_name=result.metadata.model_name,
        model_version=result.metadata.model_version,
        detection_count=len(result.detections),
        image_path=result.image_path,
        annotated_image_base64=result.annotated_image_base64,
    )


def from_engine_metadata(engine: InferenceEngine) -> ModelInfoResponse:
    return ModelInfoResponse(
        model_name=engine.metadata.model_name,
        model_version=engine.metadata.model_revision,
        is_ready=engine.is_ready,
        inference_count=engine.inference_count,
    )
