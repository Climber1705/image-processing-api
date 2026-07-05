"""
Unit tests for ObjectDetectionService.
"""

import pytest
from unittest.mock import Mock, patch
from PIL import Image
import torch

from app.services.detection.detection_service import ObjectDetectionService


@pytest.mark.unit
class TestObjectDetectionService:
    """Test cases for ObjectDetectionService."""

    @pytest.fixture
    def detection_service(self, mock_local_storage, mock_inference_engine):
        """Create ObjectDetectionService with mocked dependencies."""
        return ObjectDetectionService(
            inference_engine=mock_inference_engine,
            local_storage=mock_local_storage,
        )

    def test_get_random_colour(self, detection_service):
        """Test random color generation."""
        hex_color, rgb = detection_service._get_random_colour()
        
        assert hex_color.startswith("#")
        assert len(hex_color) == 7  # #RRGGBB
        assert len(rgb) == 3
        assert all(0 <= val <= 255 for val in rgb)

    def test_get_text_colour_dark_background(self, detection_service):
        """Test text color selection for dark background."""
        dark_rgb = (10, 10, 10)
        text_color = detection_service._get_text_colour(dark_rgb)
        
        assert text_color == "#ffffff"

    def test_get_text_colour_light_background(self, detection_service):
        """Test text color selection for light background."""
        light_rgb = (250, 250, 250)
        text_color = detection_service._get_text_colour(light_rgb)
        
        assert text_color == "#000000"

    def test_pillow_to_uploadfile(self, detection_service, sample_image_rgb):
        """Test converting PIL image to UploadFile."""
        upload_file = detection_service._pillow_to_uploadfile(sample_image_rgb, "test.png")
        
        assert upload_file.filename == "test.png"
        assert upload_file.file is not None

    def test_get_detected_objects(self, detection_service, temp_directories, mock_detr_model):
        """Test getting detected objects without visualization."""
        image_path = temp_directories["uploaded"] / "test_detect.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(image_path, format="JPEG")
        
        with patch.object(detection_service, 'processor') as mock_processor, \
             patch.object(detection_service, 'model') as mock_model:
            
            mock_outputs = Mock()
            mock_outputs.logits = Mock()
            mock_outputs.pred_boxes = Mock()
            
            mock_model.return_value = mock_outputs
            mock_model.config.id2label = {1: "person", 3: "car"}
            
            def mock_post_process(outputs, target_sizes, threshold):
                return [{
                    "scores": torch.tensor([0.95, 0.87]),
                    "labels": torch.tensor([1, 3]),
                    "boxes": torch.tensor([[100, 100, 200, 300], [300, 150, 500, 400]])
                }]
            
            mock_processor.post_process_object_detection = mock_post_process
            
            detections = detection_service.get_detected_objects(str(image_path))
            
            assert isinstance(detections, list)
            assert len(detections) > 0
            assert "label" in detections[0]
            assert "confidence" in detections[0]
            assert "box" in detections[0]

    def test_get_bounding_boxes(self, detection_service, temp_directories, mock_detr_model, mock_local_storage):
        """Test getting bounding boxes with visualization."""
        image_path = temp_directories["uploaded"] / "test_boxes.jpg"
        img = Image.new('RGB', (800, 600), color='blue')
        img.save(image_path, format="JPEG")
        
        with patch.object(detection_service, 'processor') as mock_processor, \
             patch.object(detection_service, 'model') as mock_model:
            
            mock_outputs = Mock()
            mock_model.return_value = mock_outputs
            mock_model.config.id2label = {1: "person", 3: "car"}
            
            def mock_post_process(outputs, target_sizes, threshold):
                return [{
                    "scores": torch.tensor([0.95]),
                    "labels": torch.tensor([1]),
                    "boxes": torch.tensor([[100, 100, 200, 300]])
                }]
            
            mock_processor.post_process_object_detection = mock_post_process
            
            def mock_save(file, folder, filename, format):
                output_path = temp_directories[folder] / filename
                output_path.touch()
                return str(output_path)
            
            mock_local_storage.save.side_effect = mock_save
            
            output_path = detection_service.get_bounding_boxes(str(image_path))
            
            assert output_path is not None
            assert "bounding_boxes" in output_path or "detected" in output_path