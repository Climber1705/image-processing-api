"""
Unit tests for InferenceEngine lifecycle.
"""

from unittest.mock import Mock, patch

import pytest
import torch
from app.core.config import settings
from app.dependencies.services import get_inference_service
from app.vision.inference.engine import EngineMetadata, InferenceEngine
from PIL import Image


@pytest.mark.unit
class TestInferenceEngine:
    @pytest.fixture
    def mock_detr_components(self):
        mock_processor = Mock()
        mock_model = Mock()
        mock_model.config.id2label = {1: "person"}
        mock_model.to.return_value = mock_model
        mock_model.eval.return_value = None
        return mock_processor, mock_model

    def test_from_settings_loads_model_once(self, mock_detr_model):
        with patch(
            "app.vision.inference.engine.DetrImageProcessor.from_pretrained"
        ) as load_processor, patch(
            "app.vision.inference.engine.DetrForObjectDetection.from_pretrained"
        ) as load_model:
            load_processor.return_value = mock_detr_model["processor"]
            load_model.return_value = mock_detr_model["model"]

            engine = InferenceEngine.from_settings(settings)

            assert load_processor.call_count == 1
            assert load_model.call_count == 1
            assert engine.metadata.model_name == settings.MODEL_NAME
            assert engine.is_ready is False

    def test_warmup_marks_engine_ready(self, mock_detr_components):
        mock_processor, mock_model = mock_detr_components
        mock_processor.return_value = {"pixel_values": Mock(to=lambda device: Mock())}

        engine = InferenceEngine(
            processor=mock_processor,
            model=mock_model,
            metadata=EngineMetadata(
                model_name=settings.MODEL_NAME,
                model_revision=settings.MODEL_REVISION,
            ),
            device=settings.INFERENCE_DEVICE,
        )

        engine.warmup()

        assert engine.is_ready is True
        mock_model.assert_called_once()

    def test_mark_ready_without_warmup(self, mock_detr_components):
        mock_processor, mock_model = mock_detr_components
        engine = InferenceEngine(
            processor=mock_processor,
            model=mock_model,
            metadata=EngineMetadata(
                model_name=settings.MODEL_NAME,
                model_revision=settings.MODEL_REVISION,
            ),
            device=settings.INFERENCE_DEVICE,
        )

        engine.mark_ready()

        assert engine.is_ready is True

    def test_predict_single_forward_pass(self, mock_detr_components):
        mock_processor, mock_model = mock_detr_components
        mock_processor.return_value = {"pixel_values": torch.zeros(1, 3, 64, 64)}
        mock_model.return_value = Mock()

        def mock_post_process(outputs, target_sizes, threshold):
            return [{
                "scores": torch.tensor([0.95]),
                "labels": torch.tensor([1]),
                "boxes": torch.tensor([[10.0, 20.0, 30.0, 40.0]]),
            }]

        mock_processor.post_process_object_detection = mock_post_process

        engine = InferenceEngine(
            processor=mock_processor,
            model=mock_model,
            metadata=EngineMetadata(
                model_name=settings.MODEL_NAME,
                model_revision=settings.MODEL_REVISION,
            ),
            device=settings.INFERENCE_DEVICE,
        )

        image = Image.new("RGB", (100, 100), color="red")
        result = engine.predict(image, confidence_threshold=0.5)

        assert mock_model.call_count == 1
        assert engine.inference_count == 1
        assert len(result.detections) == 1
        assert result.detections[0].label == "person"
        assert result.detections[0].confidence == pytest.approx(0.95)
        assert result.detections[0].box == [10.0, 20.0, 30.0, 40.0]
        assert result.model_name == settings.MODEL_NAME

    def test_get_inference_service_uses_shared_engine(
        self, mock_local_storage, mock_inference_engine
    ):
        request = Mock()
        request.app.state.inference_engine = mock_inference_engine
        mock_image_service = Mock()
        mock_image_repository = Mock()

        service = get_inference_service(
            request=request,
            storage=mock_local_storage,
            image_service=mock_image_service,
            image_repository=mock_image_repository,
        )

        assert service.engine is mock_inference_engine
