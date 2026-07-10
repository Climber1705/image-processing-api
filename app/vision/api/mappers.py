from app.vision.api.responses import (
    DetectionBox,
    InferenceDetectResponse,
    InferenceDetectVisualizeResponse,
    ModelInfoResponse,
)
from app.vision.domain.dtos import DetectResponseDTO
from app.vision.inference.engine import InferenceEngine


def _to_inference_response(
    result: DetectResponseDTO,
    *,
    message: str,
    include_visualization: bool = False,
) -> InferenceDetectResponse | InferenceDetectVisualizeResponse:
    base = {
        "message": message,
        "detections": [
            DetectionBox(label=d.label, confidence=d.confidence, box=d.box)
            for d in result.detections
        ],
        "model_name": result.metadata.model_name,
        "model_version": result.metadata.model_version,
        "detection_count": len(result.detections),
    }
    if include_visualization:
        return InferenceDetectVisualizeResponse(
            **base,
            image_path=result.image_path,
            annotated_image_base64=result.annotated_image_base64,
        )
    return InferenceDetectResponse(**base)


def to_inference_detect_response(result: DetectResponseDTO) -> InferenceDetectResponse:
    response = _to_inference_response(
        result,
        message="Detection completed successfully",
    )
    assert isinstance(response, InferenceDetectResponse)
    return response


def to_inference_visualize_response(
    result: DetectResponseDTO,
) -> InferenceDetectVisualizeResponse:
    response = _to_inference_response(
        result,
        message="Detection with visualization completed successfully",
        include_visualization=True,
    )
    assert isinstance(response, InferenceDetectVisualizeResponse)
    return response


def from_engine_metadata(engine: InferenceEngine) -> ModelInfoResponse:
    return ModelInfoResponse(
        model_name=engine.metadata.model_name,
        model_version=engine.metadata.model_revision,
        is_ready=engine.is_ready,
        inference_count=engine.inference_count,
    )
