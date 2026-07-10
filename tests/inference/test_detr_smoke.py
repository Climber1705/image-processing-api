"""
Smoke tests that load the real DETR model.

Excluded from PR CI and the Docker build gate. Run with:
    pytest -m inference --no-cov
"""

from io import BytesIO

import pytest
from fastapi import status
from PIL import Image


@pytest.mark.inference
class TestDetrEngineSmoke:
    def test_predict_returns_structured_result(self, detr_engine):
        image = Image.new("RGB", (640, 480), color=(100, 150, 200))
        result = detr_engine.predict(image, confidence_threshold=0.5)

        assert result.model_name == "facebook/detr-resnet-50"
        assert isinstance(result.detections, list)
        for detection in result.detections:
            assert detection.label
            assert 0.0 <= detection.confidence <= 1.0
            assert len(detection.box) == 4
            xmin, ymin, xmax, ymax = detection.box
            assert xmin <= xmax
            assert ymin <= ymax

    def test_predict_at_max_dimension(self, detr_engine):
        """Exercise the resize path used for large inputs (MAX_IMAGE_DIMENSION=1333)."""
        image = Image.new("RGB", (2000, 1500), color=(50, 100, 150))
        result = detr_engine.predict(image, confidence_threshold=0.5)

        assert result.model_name == "facebook/detr-resnet-50"
        assert isinstance(result.detections, list)


@pytest.mark.inference
class TestDetrHttpSmoke:
    def _jpeg_upload(self, size: tuple[int, int] = (640, 480)):
        image = Image.new("RGB", size, color=(120, 80, 40))
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        return ("file", ("smoke_test.jpg", buffer, "image/jpeg"))

    def test_detect_multipart(self, real_inference_client):
        response = real_inference_client.post(
            "/v1/inference/detect",
            files=[self._jpeg_upload()],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_name"] == "facebook/detr-resnet-50"
        assert "detection_count" in data
        assert "detections" in data
        assert data["detection_count"] == len(data["detections"])

    def test_health_ready_with_real_model(self, real_inference_client):
        response = real_inference_client.get("/health/ready")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["status"] == "ready"
        assert body["checks"]["model_loaded"] is True
        assert body["checks"]["warmup_complete"] is True
