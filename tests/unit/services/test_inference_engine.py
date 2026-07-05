"""
Unit tests for InferenceEngine lifecycle.
"""

import pytest
from unittest.mock import Mock, patch

from app.core.config import settings
from app.services.inference.engine import EngineMetadata, InferenceEngine


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
            "app.services.inference.engine.DetrImageProcessor.from_pretrained"
        ) as load_processor, patch(
            "app.services.inference.engine.DetrForObjectDetection.from_pretrained"
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

    def test_get_object_detection_service_uses_shared_engine(
        self, mock_local_storage, mock_inference_engine
    ):
        from app.services.detection.detection_service import get_object_detection_service

        request = Mock()
        request.app.state.inference_engine = mock_inference_engine

        service = get_object_detection_service(
            request=request,
            local_storage=mock_local_storage,
        )

        assert service.engine is mock_inference_engine
