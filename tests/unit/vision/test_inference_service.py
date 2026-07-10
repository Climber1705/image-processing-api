"""
Unit tests for InferenceService.
"""

import base64
from io import BytesIO
from unittest.mock import Mock

import pytest
from app.vision.domain.dtos import DetectionDTO, DetectResponseDTO
from app.vision.domain.errors import InferenceError, ModelNotReadyError
from app.vision.inference.schemas import DetectionResult
from app.vision.service import InferenceService
from PIL import Image


@pytest.mark.unit
class TestInferenceService:
    @pytest.fixture
    def mock_image_repository(self):
        mock = Mock()
        mock.get_or_create_image_id.return_value = "output-id"
        return mock

    @pytest.fixture
    def mock_image_service(self):
        return Mock()

    @pytest.fixture
    def inference_service(self, mock_local_storage, mock_inference_engine, mock_image_service, mock_image_repository):
        mock_inference_engine.is_ready = True
        return InferenceService(
            engine=mock_inference_engine,
            storage=mock_local_storage,
            image_service=mock_image_service,
            image_repository=mock_image_repository,
        )

    @pytest.fixture
    def sample_result(self):
        return DetectionResult(
            detections=[
                DetectionDTO(label="person", confidence=0.95, box=[100.0, 100.0, 200.0, 300.0]),
                DetectionDTO(label="car", confidence=0.87, box=[300.0, 150.0, 500.0, 400.0]),
            ],
            model_name="facebook/detr-resnet-50",
            model_version=None,
        )

    @pytest.fixture
    def sample_jpeg_bytes(self):
        img = Image.new("RGB", (800, 600), color="red")
        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    def test_image_to_bytesio(self, inference_service, sample_image_rgb):
        image_bytes = inference_service._image_to_bytesio(sample_image_rgb)

        assert image_bytes is not None
        assert image_bytes.tell() == 0
        assert len(image_bytes.read()) > 0

    def test_predict_requires_ready_engine(self, inference_service, sample_image_rgb):
        inference_service.engine.is_ready = False

        with pytest.raises(ModelNotReadyError):
            inference_service._predict(sample_image_rgb)

    def test_predict_wraps_engine_errors(self, inference_service, sample_image_rgb):
        inference_service.engine.predict.side_effect = RuntimeError("Unable to infer channel dimension format")

        with pytest.raises(InferenceError, match="Inference failed"):
            inference_service._predict(sample_image_rgb)

    def test_detect_metadata_only(self, inference_service, sample_jpeg_bytes, sample_result):
        inference_service.engine.predict.return_value = sample_result

        result = inference_service.detect(sample_jpeg_bytes)

        assert isinstance(result, DetectResponseDTO)
        assert result.image_path is None
        assert result.annotated_image_base64 is None
        assert len(result.detections) == 2
        inference_service.engine.predict.assert_called_once()

    def test_detect_visualize_without_persist(self, inference_service, sample_jpeg_bytes, sample_result):
        inference_service.engine.predict.return_value = sample_result

        result = inference_service.detect(
            sample_jpeg_bytes,
            visualize=True,
            persist=False,
        )

        assert result.image_path is None
        assert result.annotated_image_base64 is not None
        base64.b64decode(result.annotated_image_base64)
        inference_service.storage.save.assert_not_called()

    def test_detect_visualize_with_persist(
        self, inference_service, sample_jpeg_bytes, sample_result, mock_local_storage, temp_directories
    ):
        inference_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = inference_service.detect(
            sample_jpeg_bytes,
            visualize=True,
            persist=True,
            source_filename="test.jpg",
        )

        assert result.image_path is not None
        assert result.annotated_image_base64 is None
        inference_service.image_repository.upsert.assert_called_once()

    def test_detect_from_path_metadata_only(self, inference_service, temp_directories, sample_result):
        image_path = temp_directories["uploaded"] / "test_detect.jpg"
        img = Image.new("RGB", (800, 600), color="red")
        img.save(image_path, format="JPEG")

        inference_service.engine.predict.return_value = sample_result

        result = inference_service.detect_from_path(str(image_path))

        assert isinstance(result, DetectResponseDTO)
        assert result.image_path is None
        assert len(result.detections) == 2
        assert result.detections[0].label == "person"
        assert result.metadata.model_name == "facebook/detr-resnet-50"
        inference_service.engine.predict.assert_called_once()

    def test_detect_from_path_with_visualization(
        self, inference_service, temp_directories, sample_result, mock_local_storage
    ):
        image_path = temp_directories["uploaded"] / "test_boxes.jpg"
        img = Image.new("RGB", (800, 600), color="blue")
        img.save(image_path, format="JPEG")

        inference_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = inference_service.detect_from_path(
            str(image_path),
            visualize=True,
            persist=True,
            source_filename="test_boxes.jpg",
        )

        assert isinstance(result, DetectResponseDTO)
        assert result.image_path is not None
        assert len(result.detections) == 2
        assert result.metadata.model_name == "facebook/detr-resnet-50"
        inference_service.engine.predict.assert_called_once()
        inference_service.image_repository.upsert.assert_called_once()

    def test_detect_from_path_single_inference(
        self, inference_service, temp_directories, sample_result, mock_local_storage
    ):
        image_path = temp_directories["uploaded"] / "test_single.jpg"
        img = Image.new("RGB", (800, 600), color="green")
        img.save(image_path, format="JPEG")

        inference_service.engine.predict.return_value = sample_result

        def mock_save(file, folder, storage_id, format="JPEG"):
            ext = ".jpg" if format.upper() == "JPEG" else f".{format.lower()}"
            output_path = temp_directories[folder] / f"{storage_id}{ext}"
            output_path.touch()
            return str(output_path)

        mock_local_storage.save.side_effect = mock_save

        result = inference_service.detect_from_path(
            str(image_path),
            visualize=True,
            persist=True,
            source_filename="test_single.jpg",
        )

        assert result.image_path is not None
        assert len(result.detections) == 2
        inference_service.engine.predict.assert_called_once()
