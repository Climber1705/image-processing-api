"""
Unit tests for inference visualizer.
"""

import pytest
from app.vision.domain.dtos import DetectionDTO
from app.vision.inference.visualizer import draw_bounding_boxes
from PIL import Image


@pytest.mark.unit
class TestVisualizer:
    def test_draw_bounding_boxes(self):
        image = Image.new("RGB", (200, 200), color="white")
        detections = [
            DetectionDTO(label="person", confidence=0.95, box=[10.0, 10.0, 50.0, 80.0]),
        ]

        result = draw_bounding_boxes(image, detections)

        assert isinstance(result, Image.Image)
        assert result.size == image.size
        assert result is not image
