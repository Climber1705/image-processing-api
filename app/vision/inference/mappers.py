from app.vision.domain.dtos import (
    DetectionDTO,
    DetectResponseDTO,
    InferenceMetadataDTO,
)
from app.vision.inference.schemas import DetectionResult, EngineMetadata


def to_detection_dtos(
    scores,
    labels,
    boxes,
    id2label: dict[int, str],
) -> list[DetectionDTO]:
    return [
        DetectionDTO(
            label=id2label[label.item()],
            confidence=score.item(),
            box=box.tolist(),
        )
        for score, label, box in zip(scores, labels, boxes, strict=True)
    ]


def to_detection_result(
    detections: list[DetectionDTO],
    metadata: EngineMetadata,
) -> DetectionResult:
    return DetectionResult(
        detections=detections,
        model_name=metadata.model_name,
        model_version=metadata.model_revision,
    )


def to_detect_response_dto(
    result: DetectionResult,
    image_path: str | None = None,
    annotated_image_base64: str | None = None,
) -> DetectResponseDTO:
    return DetectResponseDTO(
        detections=result.detections,
        metadata=InferenceMetadataDTO(
            model_name=result.model_name,
            model_version=result.model_version,
        ),
        image_path=image_path,
        annotated_image_base64=annotated_image_base64,
    )
