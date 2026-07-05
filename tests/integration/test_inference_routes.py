"""
Integration tests for /v1/inference API routes.
"""

from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from app.dependencies.repositories import get_image_repository
from app.dependencies.services import get_image_service, get_inference_service
from app.dependencies.storage import get_local_image_storage
from app.main import app
from app.vision.domain.dtos import DetectionDTO
from app.vision.inference.schemas import DetectionResult
from app.vision.service import InferenceService
from fastapi import status
from fastapi.testclient import TestClient
from PIL import Image


@pytest.fixture
def inference_client(
    temp_directories,
    mock_local_storage,
    mock_image_service,
    mock_inference_engine,
):
    """Test client with real InferenceService and mocked engine."""
    from app.media.repository import ImageRepository

    image_repository = Mock(spec=ImageRepository)
    image_repository.get_or_create_image_id.return_value = "output-id"

    inference_service = InferenceService(
        engine=mock_inference_engine,
        storage=mock_local_storage,
        image_service=mock_image_service,
        image_repository=image_repository,
    )

    def override_get_local_image_storage():
        return mock_local_storage

    def override_get_image_service():
        return mock_image_service

    def override_get_inference_service():
        return inference_service

    def override_get_image_repository():
        return image_repository

    app.dependency_overrides[get_local_image_storage] = override_get_local_image_storage
    app.dependency_overrides[get_image_service] = override_get_image_service
    app.dependency_overrides[get_inference_service] = override_get_inference_service
    app.dependency_overrides[get_image_repository] = override_get_image_repository

    sample_result = DetectionResult(
        detections=[
            DetectionDTO(label="person", confidence=0.95, box=[100.0, 100.0, 200.0, 300.0]),
        ],
        model_name="facebook/detr-resnet-50",
        model_version=None,
    )
    mock_inference_engine.is_ready = True
    mock_inference_engine.predict.return_value = sample_result

    with patch(
        "app.core.lifespan.InferenceEngine.from_settings",
        return_value=mock_inference_engine,
    ):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


@pytest.mark.integration
class TestInferenceRoutes:
    def _make_jpeg_file(self):
        img = Image.new("RGB", (100, 100), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return ("file", ("test.jpg", buffer, "image/jpeg"))

    def test_detect_multipart(self, inference_client):
        response = inference_client.post(
            "/v1/inference/detect",
            files=[self._make_jpeg_file()],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["detection_count"] == 1
        assert data["detections"][0]["label"] == "person"
        assert data["model_name"] == "facebook/detr-resnet-50"

    def test_detect_visualize_without_persist(self, inference_client):
        response = inference_client.post(
            "/v1/inference/detect/visualize?persist=false",
            files=[self._make_jpeg_file()],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["annotated_image_base64"] is not None
        assert data.get("image_path") is None

    def test_detect_by_reference(self, inference_client, temp_directories, mock_image_service):
        image_path = temp_directories["uploaded"] / "ref.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(image_path, format="JPEG")
        mock_image_service.get_image_path.return_value = image_path

        response = inference_client.post(
            "/v1/inference/detect?image_name=ref.jpg&folder=uploaded",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["detection_count"] == 1

    def test_detect_missing_input(self, inference_client):
        response = inference_client.post("/v1/inference/detect")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_models(self, inference_client, mock_inference_engine):
        response = inference_client.get("/v1/inference/models")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["model_name"] == "facebook/detr-resnet-50"
        assert data["is_ready"] is True

    def test_detect_engine_not_ready(self, inference_client, mock_inference_engine):
        mock_inference_engine.is_ready = False

        response = inference_client.post(
            "/v1/inference/detect",
            files=[self._make_jpeg_file()],
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
