"""Unit tests for media domain exception handlers."""

import json

import pytest
from starlette.requests import Request

from app.media.api.handlers import image_not_found_handler, invalid_folder_handler
from app.media.domain.errors import ImageNotFoundError, InvalidFolderError


def _make_request() -> Request:
    return Request({"type": "http", "method": "GET", "path": "/", "headers": []})


@pytest.mark.unit
class TestMediaExceptionHandlers:
    @pytest.mark.asyncio
    async def test_image_not_found_handler_returns_detail_message(self):
        exc = ImageNotFoundError("Image missing.jpg not found in uploaded")
        response = await image_not_found_handler(_make_request(), exc)

        assert response.status_code == 404
        assert json.loads(response.body) == {
            "detail": "Image missing.jpg not found in uploaded",
        }

    @pytest.mark.asyncio
    async def test_invalid_folder_handler_returns_detail_message(self):
        exc = InvalidFolderError("Invalid folder: archive")
        response = await invalid_folder_handler(_make_request(), exc)

        assert response.status_code == 400
        assert json.loads(response.body) == {"detail": "Invalid folder: archive"}
