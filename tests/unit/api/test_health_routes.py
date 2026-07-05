"""
Unit tests for health check endpoints.
"""

import pytest
from unittest.mock import Mock, patch

from app.vision.inference.engine import EngineMetadata


@pytest.mark.unit
class TestHealthRoutes:
    def test_health_live(self, test_client):
        response = test_client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_health_ready_when_engine_ready(self, test_client, mock_inference_engine):
        mock_inference_engine.is_ready = True
        mock_inference_engine.metadata = EngineMetadata(
            model_name="facebook/detr-resnet-50",
            model_revision=None,
        )

        response = test_client.get("/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["model_loaded"] is True
        assert data["checks"]["warmup_complete"] is True
        assert data["checks"]["storage_writable"] is True
        assert data["model_name"] == "facebook/detr-resnet-50"

    def test_health_ready_not_ready_without_warmup(self, test_client, mock_inference_engine):
        mock_inference_engine.is_ready = False
        mock_inference_engine.metadata = EngineMetadata(
            model_name="facebook/detr-resnet-50",
            model_revision=None,
        )

        response = test_client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["warmup_complete"] is False

    def test_health_ready_storage_not_writable(self, test_client, mock_inference_engine, temp_directories):
        mock_inference_engine.is_ready = True
        mock_inference_engine.metadata = EngineMetadata(
            model_name="facebook/detr-resnet-50",
            model_revision=None,
        )

        with patch("app.api.routes.health.storage_dirs_writable", return_value=False):
            response = test_client.get("/health/ready")

        assert response.status_code == 503
        assert response.json()["checks"]["storage_writable"] is False
