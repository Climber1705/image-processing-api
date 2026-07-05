from app.vision.api.responses import (
    BoundingBoxResponse,
    DetectedObjectsResponse,
    DetectionBox,
)
from app.vision.domain.dtos import DetectionsResultDTO, DetectResponseDTO


def _to_detection_boxes(detections) -> list[DetectionBox]:
    return [
        DetectionBox(label=d.label, confidence=d.confidence, box=d.box)
        for d in detections
    ]


def to_bounding_box_response(result: DetectResponseDTO) -> BoundingBoxResponse:
    return BoundingBoxResponse(
        message="Bounding boxes drawn successfully",
        image_path=result.image_path,
        detections=_to_detection_boxes(result.detections),
        model_name=result.metadata.model_name,
        model_version=result.metadata.model_version,
        detection_count=len(result.detections),
    )


def to_detected_objects_response(result: DetectionsResultDTO) -> DetectedObjectsResponse:
    return DetectedObjectsResponse(
        message="Detected objects retrieved successfully",
        detected_objects=_to_detection_boxes(result.detections),
        model_name=result.metadata.model_name,
        model_version=result.metadata.model_version,
        detection_count=len(result.detections),
    )
