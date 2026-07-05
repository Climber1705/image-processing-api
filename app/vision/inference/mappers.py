from app.vision.domain.dtos import (
    DetectionDTO,
    DetectionsResultDTO,
    DetectResponseDTO,
    InferenceMetadataDTO,
)
from app.vision.inference.schemas import Detection, DetectionResult, EngineMetadata


def to_detection(label: str, confidence: float, box: list[float]) -> Detection:
    return Detection(label=label, confidence=confidence, box=box)


def to_detections_from_raw(
    scores,
    labels,
    boxes,
    id2label: dict[int, str],
) -> list[Detection]:
    return [
        to_detection(
            label=id2label[label.item()],
            confidence=score.item(),
            box=box.tolist(),
        )
        for score, label, box in zip(scores, labels, boxes)
    ]


def to_detection_result(
    detections: list[Detection],
    metadata: EngineMetadata,
) -> DetectionResult:
    return DetectionResult(
        detections=detections,
        model_name=metadata.model_name,
        model_version=metadata.model_revision,
    )


def to_detection_dto(detection: Detection) -> DetectionDTO:
    return DetectionDTO(
        label=detection.label,
        confidence=detection.confidence,
        box=detection.box,
    )


def to_detection_dtos(detections: list[Detection]) -> list[DetectionDTO]:
    return [to_detection_dto(detection) for detection in detections]


def to_inference_metadata(result: DetectionResult) -> InferenceMetadataDTO:
    return InferenceMetadataDTO(
        model_name=result.model_name,
        model_version=result.model_version,
    )


def to_detections_result_dto(result: DetectionResult) -> DetectionsResultDTO:
    return DetectionsResultDTO(
        detections=to_detection_dtos(result.detections),
        metadata=to_inference_metadata(result),
    )


def to_detect_response_dto(result: DetectionResult, image_path: str) -> DetectResponseDTO:
    base = to_detections_result_dto(result)
    return DetectResponseDTO(
        image_path=image_path,
        detections=base.detections,
        metadata=base.metadata,
    )
