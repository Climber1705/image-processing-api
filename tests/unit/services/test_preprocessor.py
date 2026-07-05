"""
Unit tests for inference preprocessor.
"""

import pytest
from PIL import Image
from unittest.mock import Mock

from app.services.inference.preprocessor import load_image, preprocess, resize_if_needed


@pytest.mark.unit
class TestPreprocessor:
    def test_resize_if_needed_downscales_large_image(self):
        image = Image.new("RGB", (2000, 1500), color="red")
        resized = resize_if_needed(image, max_dimension=1333)

        assert max(resized.size) == 1333

    def test_resize_if_needed_keeps_small_image(self):
        image = Image.new("RGB", (800, 600), color="red")
        resized = resize_if_needed(image, max_dimension=1333)

        assert resized.size == (800, 600)

    def test_preprocess_moves_tensors_to_device(self, temp_directories):
        image_path = temp_directories["uploaded"] / "preprocess_test.jpg"
        Image.new("RGB", (100, 100), color="blue").save(image_path)

        mock_processor = Mock()
        pixel_values = Mock()
        pixel_values.to.return_value = "on_device"
        mock_processor.return_value = {"pixel_values": pixel_values}

        inputs = preprocess(load_image(str(image_path)), mock_processor, device="cpu", max_dimension=1333)

        assert inputs["pixel_values"] == "on_device"
        pixel_values.to.assert_called_once_with("cpu")
