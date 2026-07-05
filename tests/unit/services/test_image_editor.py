"""
Unit tests for ImageEditService.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock
from PIL import Image

from app.editing.image_editor import ImageEditService
from app.storage.local_storage import LocalImageStorage


@pytest.mark.unit
class TestImageEditService:
    """Test cases for ImageEditService."""

    @pytest.fixture
    def edit_service(self, temp_directories, mock_image_validator):
        """Create ImageEditService with real storage and mocked CRUD."""
        mock_image_service = Mock()

        def get_image_path_side_effect(image_name: str, folder: str = "uploaded") -> Path:
            return temp_directories.get(folder, temp_directories["uploaded"]) / image_name

        mock_image_service.get_image_path.side_effect = get_image_path_side_effect

        mock_image_repository = Mock()
        mock_image_repository.resolve_image_id.return_value = "11111111-1111-1111-1111-111111111111"

        storage = LocalImageStorage(
            directories=temp_directories,
            format_helper=mock_image_validator,
        )

        return ImageEditService(
            image_service=mock_image_service,
            image_repository=mock_image_repository,
            storage=storage,
        )

    def test_build_display_filename_with_suffix(self, edit_service):
        """Test display filename generation with suffix."""
        assert edit_service._build_display_filename("test.jpg", "resized") == "test_resized.jpg"

    def test_build_display_filename_without_suffix(self, edit_service):
        """Test display filename generation without suffix."""
        assert edit_service._build_display_filename("test.jpg") == "test.jpg"

    def test_resize_image(self, edit_service, temp_directories):
        """Test image resizing stores file by UUID and registers display name."""
        source_path = temp_directories["uploaded"] / "test_resize.jpg"
        img = Image.new('RGB', (800, 600), color='red')
        img.save(source_path, format="JPEG")

        output_path = edit_service.resize_image("test_resize.jpg", 400, 300)

        assert Path(output_path).exists()
        assert Path(output_path).name == "11111111-1111-1111-1111-111111111111.jpg"

        with Image.open(output_path) as resized_img:
            assert resized_img.width == 400
            assert resized_img.height == 300

        edit_service.image_repository.create_record.assert_called_once()
        call_kwargs = edit_service.image_repository.create_record.call_args.kwargs
        assert call_kwargs["display_filename"] == "test_resize_resized.jpg"

    def test_rotate_image(self, edit_service, temp_directories):
        """Test image rotation."""
        source_path = temp_directories["uploaded"] / "test_rotate.jpg"
        img = Image.new('RGB', (100, 200), color='blue')
        img.save(source_path, format="JPEG")

        output_path = edit_service.rotate_image("test_rotate.jpg", 90, expand=True)

        assert Path(output_path).exists()

    def test_rotate_image_without_expand(self, edit_service, temp_directories):
        """Test image rotation without expanding canvas."""
        source_path = temp_directories["uploaded"] / "test_rotate2.jpg"
        img = Image.new('RGB', (100, 200), color='green')
        img.save(source_path, format="JPEG")

        output_path = edit_service.rotate_image("test_rotate2.jpg", 45, expand=False)

        assert Path(output_path).exists()

    def test_convert_to_grayscale(self, edit_service, temp_directories):
        """Test converting image to grayscale."""
        source_path = temp_directories["uploaded"] / "test_gray.jpg"
        img = Image.new('RGB', (100, 100), color='red')
        img.save(source_path, format="JPEG")

        output_path = edit_service.convert_to_grayscale("test_gray.jpg")

        assert Path(output_path).exists()

        with Image.open(output_path) as gray_img:
            assert gray_img.mode in ['L', 'LA', 'P', 'RGB']

    def test_blur_image(self, edit_service, temp_directories):
        """Test applying blur filter."""
        source_path = temp_directories["uploaded"] / "test_blur.jpg"
        img = Image.new('RGB', (100, 100), color='yellow')
        img.save(source_path, format="JPEG")

        output_path = edit_service.blur_image("test_blur.jpg", radius=5.0)

        assert Path(output_path).exists()

    def test_sharpen_image(self, edit_service, temp_directories):
        """Test applying sharpen filter."""
        source_path = temp_directories["uploaded"] / "test_sharpen.jpg"
        img = Image.new('RGB', (100, 100), color='purple')
        img.save(source_path, format="JPEG")

        output_path = edit_service.sharpen_image("test_sharpen.jpg", factor=2.0, radius=2.0, threshold=3)

        assert Path(output_path).exists()

    def test_adjust_brightness(self, edit_service, temp_directories):
        """Test adjusting image brightness."""
        source_path = temp_directories["uploaded"] / "test_brightness.jpg"
        img = Image.new('RGB', (100, 100), color='orange')
        img.save(source_path, format="JPEG")

        output_path = edit_service.adjust_brightness("test_brightness.jpg", factor=1.5)

        assert Path(output_path).exists()

    def test_adjust_contrast(self, edit_service, temp_directories):
        """Test adjusting image contrast."""
        source_path = temp_directories["uploaded"] / "test_contrast.jpg"
        img = Image.new('RGB', (100, 100), color='cyan')
        img.save(source_path, format="JPEG")

        output_path = edit_service.adjust_contrast("test_contrast.jpg", factor=1.2)

        assert Path(output_path).exists()

    def test_process_image_error_handling(self, edit_service):
        """Test error handling in _process_image."""
        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            edit_service._process_image(
                "nonexistent.jpg",
                lambda img, **kwargs: img,
                suffix="test"
            )
