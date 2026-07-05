"""Integration tests for media domain errors through real services."""

import pytest
from fastapi import status


@pytest.mark.integration
class TestMediaDomainErrorsRealService:
    def test_get_missing_image_returns_404_with_detail(self, test_client_real_media):
        response = test_client_real_media.get("/images/missing.jpg?folder=uploaded")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Image missing.jpg not found in uploaded"

    def test_delete_missing_image_returns_404_with_detail(self, test_client_real_media):
        response = test_client_real_media.delete("/images/missing.jpg?folder=uploaded")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_move_missing_image_returns_404_with_detail(self, test_client_real_media):
        response = test_client_real_media.patch(
            "/images/missing.jpg",
            json={"source_folder": "uploaded", "target_folder": "edited"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_invalid_folder_query_returns_422(self, test_client_real_media):
        response = test_client_real_media.delete("/images?folder=invalid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
