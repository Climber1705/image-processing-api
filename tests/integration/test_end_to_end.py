"""
End-to-end integration tests for complete workflows.

Uses test_client_full_stack: real SQLite, storage, media/edit/inference services;
only the DETR model weights are mocked.
"""

from io import BytesIO
from pathlib import Path

import pytest
from fastapi import status
from PIL import Image


def _jpeg_upload(name: str = "workflow_test.jpg", color: str = "red", size: tuple[int, int] = (800, 600)):
    img = Image.new("RGB", size, color=color)
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return {"file": (name, buffer, "image/jpeg")}


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end workflow tests against real services."""

    def test_upload_edit_detect_workflow(self, test_client_full_stack, temp_directories):
        """Upload -> resize -> detect with persistence through real services."""
        upload_response = test_client_full_stack.post(
            "/images",
            files=_jpeg_upload(),
            data={"filename": "workflow_test", "format": "JPEG"},
        )
        assert upload_response.status_code == status.HTTP_201_CREATED
        upload_body = upload_response.json()
        assert upload_body["status"] == "success"
        assert Path(upload_body["path"]).exists()

        resize_response = test_client_full_stack.post(
            "/images/workflow_test.jpg/edits/resize?width=400&height=300",
        )
        assert resize_response.status_code == status.HTTP_200_OK
        edit_body = resize_response.json()
        edited_path = Path(edit_body["path"])
        assert edited_path.exists()
        with Image.open(edited_path) as edited:
            assert edited.width == 400
            assert edited.height == 300

        detect_response = test_client_full_stack.post(
            "/v1/inference/detect/visualize?persist=true",
            files=_jpeg_upload(),
        )
        assert detect_response.status_code == status.HTTP_200_OK
        detect_body = detect_response.json()
        assert detect_body["detection_count"] >= 1
        assert detect_body["image_path"] is not None
        assert Path(detect_body["image_path"]).exists()

    def test_upload_move_delete_workflow(self, test_client_full_stack, temp_directories):
        """Upload -> move -> delete through real services."""
        upload_response = test_client_full_stack.post(
            "/images",
            files=_jpeg_upload("move_test.jpg", color="blue", size=(100, 100)),
            data={"filename": "move_test", "format": "JPEG"},
        )
        assert upload_response.status_code == status.HTTP_201_CREATED

        move_response = test_client_full_stack.patch(
            "/images/move_test.jpg",
            json={"source_folder": "uploaded", "target_folder": "edited"},
        )
        assert move_response.status_code == status.HTTP_200_OK
        assert Path(move_response.json()["path"]).exists()
        assert not any(temp_directories["uploaded"].rglob("move_test.jpg"))
        assert any(temp_directories["edited"].rglob("move_test.jpg"))

        delete_response = test_client_full_stack.delete("/images/move_test.jpg?folder=edited")
        assert delete_response.status_code == status.HTTP_200_OK
        assert not any(temp_directories["edited"].rglob("move_test.jpg"))

    def test_multiple_edits_on_same_image(self, test_client_full_stack):
        """Apply multiple edits after a real upload."""
        upload_response = test_client_full_stack.post(
            "/images",
            files=_jpeg_upload("multi_edit.jpg", color="green"),
            data={"filename": "multi_edit", "format": "JPEG"},
        )
        assert upload_response.status_code == status.HTTP_201_CREATED

        edits = [
            "/images/multi_edit.jpg/edits/grayscale",
            "/images/multi_edit.jpg/edits/resize?width=400&height=300",
            "/images/multi_edit.jpg/edits/brightness?factor=1.2",
        ]
        for endpoint in edits:
            response = test_client_full_stack.post(endpoint)
            assert response.status_code == status.HTTP_200_OK
            assert Path(response.json()["path"]).exists()

    def test_error_recovery_scenario(self, test_client_full_stack):
        """Missing resources return consistent 404 responses."""
        response = test_client_full_stack.post(
            "/images/nonexistent.jpg/edits/resize?width=400&height=300",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

        delete_response = test_client_full_stack.delete(
            "/images/nonexistent.jpg?folder=uploaded",
        )
        assert delete_response.status_code == status.HTTP_404_NOT_FOUND
