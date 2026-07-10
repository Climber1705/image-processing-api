"""
Unit tests for ImageEditService.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from app.editing.domain.errors import ImageEditError
from app.editing.service import ImageEditService
from app.media.domain.dtos import ImageDTO
from app.media.utils.filename import build_display_filename
from app.storage.local_storage import LocalImageStorage
from PIL import Image


def _make_image_dto(**overrides) -> ImageDTO:
    defaults = {
        "id": "11111111-1111-1111-1111-111111111111",
        "filename": "test.jpg",
        "format": "JPEG",
        "mode": "RGB",
        "width": 100,
        "height": 100,
        "size_bytes": 1024,
        "path": "/tmp/test.jpg",
        "folder": "edited",
    }
    defaults.update(overrides)
    return ImageDTO(**defaults)


@pytest.mark.unit
class TestImageEditService:
    """Test cases for ImageEditService."""

    @pytest.fixture
    def edit_service(self, temp_directories, format_extensions):
        """Create ImageEditService with real storage and mocked CRUD."""
        mock_image_service = Mock()

        def get_image_path_side_effect(image_name: str, folder: str = "uploaded") -> Path:
            return temp_directories.get(folder, temp_directories["uploaded"]) / image_name

        mock_image_service.get_image_path.side_effect = get_image_path_side_effect

        mock_image_repository = Mock()
        mock_image_repository.get_or_create_image_id.return_value = "11111111-1111-1111-1111-111111111111"
        mock_image_repository.upsert.side_effect = lambda **kwargs: _make_image_dto(
            path=str(kwargs["path"]),
            filename=kwargs["display_filename"],
            id=kwargs["image_id"],
        )

        storage = LocalImageStorage(
            directories=temp_directories,
            format_extensions=format_extensions,
        )

        return ImageEditService(
            image_service=mock_image_service,
            image_repository=mock_image_repository,
            storage=storage,
        )

    def test_build_display_filename_with_suffix(self):
        """Test display filename generation with suffix."""
        assert build_display_filename("test.jpg", "resized") == "test_resized.jpg"

    def test_build_display_filename_without_suffix(self):
        """Test display filename generation without suffix."""
        assert build_display_filename("test.jpg") == "test.jpg"

    def test_resize_image(self, edit_service, temp_directories):
        """Test image resizing stores file by UUID and registers display name."""
        source_path = temp_directories["uploaded"] / "test_resize.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(source_path, format="JPEG")

        result = edit_service.resize_image("test_resize.jpg", 400, 300)

        assert Path(result.path).exists()
        assert Path(result.path).name == "11111111-1111-1111-1111-111111111111.jpg"

        with Image.open(result.path) as resized_img:
            assert resized_img.width == 400
            assert resized_img.height == 300

        edit_service.image_repository.upsert.assert_called_once()
        call_kwargs = edit_service.image_repository.upsert.call_args.kwargs
        assert call_kwargs["display_filename"] == "test_resize_resized.jpg"

    def test_rotate_image(self, edit_service, temp_directories):
        """Test image rotation."""
        source_path = temp_directories["uploaded"] / "test_rotate.jpg"
        img = Image.new('RGB', (100, 200), color='blue')
        img.save(source_path, format="JPEG")

        result = edit_service.rotate_image("test_rotate.jpg", 90, expand=True)

        assert Path(result.path).exists()

    def test_rotate_image_without_expand(self, edit_service, temp_directories):
        """Test image rotation without expanding canvas."""
        source_path = temp_directories["uploaded"] / "test_rotate2.jpg"
        img = Image.new('RGB', (100, 200), color='green')
        img.save(source_path, format="JPEG")

        result = edit_service.rotate_image("test_rotate2.jpg", 45, expand=False)

        assert Path(result.path).exists()

    def test_convert_to_grayscale(self, edit_service, temp_directories):
        """Test converting image to grayscale."""
        source_path = temp_directories["uploaded"] / "test_gray.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(source_path, format="JPEG")

        result = edit_service.convert_to_grayscale("test_gray.jpg")

        assert Path(result.path).exists()

        with Image.open(result.path) as gray_img:
            assert gray_img.mode in ['L', 'LA', 'P', 'RGB']

    def test_blur_image(self, edit_service, temp_directories):
        """Test applying blur filter."""
        source_path = temp_directories["uploaded"] / "test_blur.jpg"
        img = Image.new('RGB', (100, 100), color='yellow')
        img.save(source_path, format="JPEG")

        result = edit_service.blur_image("test_blur.jpg", radius=5.0)

        assert Path(result.path).exists()

    def test_sharpen_image(self, edit_service, temp_directories):
        """Test applying sharpen filter."""
        source_path = temp_directories["uploaded"] / "test_sharpen.jpg"
        img = Image.new('RGB', (100, 100), color='purple')
        img.save(source_path, format="JPEG")

        result = edit_service.sharpen_image("test_sharpen.jpg", factor=2.0, radius=2.0, threshold=3)

        assert Path(result.path).exists()

    def test_adjust_brightness(self, edit_service, temp_directories):
        """Test adjusting image brightness."""
        source_path = temp_directories["uploaded"] / "test_brightness.jpg"
        img = Image.new('RGB', (100, 100), color='orange')
        img.save(source_path, format="JPEG")

        result = edit_service.adjust_brightness("test_brightness.jpg", factor=1.5)

        assert Path(result.path).exists()

    def test_adjust_contrast(self, edit_service, temp_directories):
        """Test adjusting image contrast."""
        source_path = temp_directories["uploaded"] / "test_contrast.jpg"
        img = Image.new('RGB', (100, 100), color='cyan')
        img.save(source_path, format="JPEG")

        result = edit_service.adjust_contrast("test_contrast.jpg", factor=1.2)

        assert Path(result.path).exists()

    def test_apply_edit_error_handling(self, edit_service):
        """Test error handling in _apply_edit."""
        with pytest.raises(ImageEditError):
            edit_service._apply_edit(
                "nonexistent.jpg",
                lambda img, **kwargs: img,
                suffix="test",
            )
