"""Fixtures for real-model inference tests (slow; excluded from fast CI)."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


@pytest.fixture(scope="module")
def detr_engine():
    """Load and warm up DETR once per module — avoids re-downloading weights per test."""
    from app.core.config import get_settings
    from app.vision.inference.engine import InferenceEngine

    settings = get_settings()
    engine = InferenceEngine.from_settings(settings)
    engine.warmup()
    return engine


@pytest.fixture(scope="module")
def real_inference_client(detr_engine):
    """HTTP client backed by a real warmed-up InferenceEngine."""
    with patch(
        "app.core.lifespan.InferenceEngine.from_settings",
        return_value=detr_engine,
    ):
        with TestClient(app) as client:
            yield client
