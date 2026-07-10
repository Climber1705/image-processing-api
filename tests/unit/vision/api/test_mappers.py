"""
Unit tests for vision API mappers.
"""

from unittest.mock import Mock

import pytest
from app.vision.api.mappers import (
    from_engine_metadata,
    to_inference_detect_response,
    to_inference_visualize_response,
)
from app.vision.domain.dtos import (
    DetectionDTO,
    DetectResponseDTO,
    InferenceMetadataDTO,
)


@pytest.mark.unit
class TestVisionApiMappers:
    @pytest.fixture
    def metadata(self):
        return InferenceMetadataDTO(model_name="facebook/detr-resnet-50", model_version=None)

    @pytest.fixture
    def detections(self):
        return [DetectionDTO(label="person", confidence=0.95, box=[1.0, 2.0, 3.0, 4.0])]

    def test_to_inference_detect_response(self, detections, metadata):
        dto = DetectResponseDTO(detections=detections, metadata=metadata)
        response = to_inference_detect_response(dto)

        assert response.detection_count == 1
        assert response.detections[0].label == "person"

    def test_to_inference_visualize_response_with_base64(self, detections, metadata):
        dto = DetectResponseDTO(
            detections=detections,
            metadata=metadata,
            annotated_image_base64="abc123",
        )
        response = to_inference_visualize_response(dto)

        assert response.annotated_image_base64 == "abc123"
        assert response.image_path is None

    def test_from_engine_metadata(self):
        engine = Mock()
        engine.metadata.model_name = "facebook/detr-resnet-50"
        engine.metadata.model_revision = None
        engine.is_ready = True
        engine.inference_count = 3

        response = from_engine_metadata(engine)

        assert response.model_name == "facebook/detr-resnet-50"
        assert response.is_ready is True
        assert response.inference_count == 3
