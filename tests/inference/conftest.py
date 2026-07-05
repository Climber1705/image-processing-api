"""Fixtures for real-model inference tests (slow; excluded from fast CI)."""

from importlib.util import find_spec
from unittest.mock import patch

import pytest
from app.main import app
from fastapi.testclient import TestClient

INFERENCE_DEPS = ("torch", "transformers", "timm")


def _missing_inference_deps() -> list[str]:
    return [name for name in INFERENCE_DEPS if find_spec(name) is None]


@pytest.fixture(scope="module")
def detr_engine():
    """Load and warm up DETR once per module — avoids re-downloading weights per test."""
    missing = _missing_inference_deps()
    if missing:
        pytest.skip(
            "Inference smoke tests require ML dependencies. "
            f"Missing: {', '.join(missing)}. "
            "Install with: pip install -e \".[test]\""
        )

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
