"""
End-to-end integration tests for complete workflows.
"""

import pytest
from io import BytesIO
from PIL import Image
from fastapi import status


@pytest.mark.integration
class TestEndToEndWorkflows:
    """End-to-end workflow tests."""

    def test_upload_edit_detect_workflow(self, test_client_with_overrides, temp_directories):
        """Test complete workflow: upload -> edit -> detect."""
        img = Image.new('RGB', (800, 600), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"file": ("workflow_test.jpg", img_bytes, "image/jpeg")}
        upload_response = test_client_with_overrides.post(
            "/images",
            files=files,
            data={"filename": "workflow_test", "format": "JPEG"}
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        
        image_path = temp_directories["uploaded"] / "workflow_test.jpg"
        img.save(image_path, format='JPEG')
        
        resize_response = test_client_with_overrides.post(
            "/images/workflow_test.jpg/edits/resize?width=400&height=300"
        )
        
        assert resize_response.status_code == status.HTTP_200_OK
        
        img_bytes.seek(0)
        detect_response = test_client_with_overrides.post(
            "/v1/inference/detect/visualize?persist=true",
            files={"file": ("workflow_test.jpg", img_bytes, "image/jpeg")},
        )

        assert detect_response.status_code == status.HTTP_200_OK

    def test_upload_move_delete_workflow(self, test_client_with_overrides, temp_directories):
        """Test complete workflow: upload -> move -> delete."""
        img = Image.new('RGB', (100, 100), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        files = {"file": ("move_test.jpg", img_bytes, "image/jpeg")}
        upload_response = test_client_with_overrides.post(
            "/images",
            files=files,
            data={"filename": "move_test", "format": "JPEG"}
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        
        image_path = temp_directories["uploaded"] / "move_test.jpg"
        img.save(image_path, format='JPEG')
        
        move_data = {"source_folder": "uploaded", "target_folder": "edited"}
        move_response = test_client_with_overrides.patch(
            "/images/move_test.jpg",
            json=move_data
        )
        
        assert move_response.status_code == status.HTTP_200_OK
        
        
        delete_response = test_client_with_overrides.delete(
            "/images/move_test.jpg?folder=edited"
        )
        
        assert delete_response.status_code == status.HTTP_200_OK

    def test_multiple_edits_on_same_image(self, test_client_with_overrides, temp_directories):
        """Test applying multiple edits to the same image."""
        img_path = temp_directories["uploaded"] / "multi_edit.jpg"
        img = Image.new('RGB', (800, 600), color='green')
        img.save(img_path, format="JPEG")
        
        edits = [
            ("/images/multi_edit.jpg/edits/grayscale", "POST"),
            ("/images/multi_edit.jpg/edits/resize?width=400&height=300", "POST"),
            ("/images/multi_edit.jpg/edits/brightness?factor=1.2", "POST")
        ]
        
        for endpoint, method in edits:
            if method == "POST":
                response = test_client_with_overrides.post(endpoint)
                assert response.status_code == status.HTTP_200_OK

    def test_error_recovery_scenario(self, test_client_with_overrides):
        """Test error recovery scenarios."""
        response = test_client_with_overrides.post(
            "/images/nonexistent.jpg/edits/resize?width=400&height=300"
        )
        
        assert response.status_code in [404, 500]
        
        delete_response = test_client_with_overrides.delete(
            "/images/nonexistent.jpg?folder=uploaded"
        )
        
        assert delete_response.status_code == status.HTTP_404_NOT_FOUND



