"""
Unit tests for ImageService.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest
from app.media.domain.dtos import ImageDTO
from app.media.domain.enums import ImageFolder
from app.media.domain.errors import (
    ImageConflictError,
    ImageNotFoundError,
    InvalidFolderError,
    InvalidMoveError,
)
from app.media.service import ImageService
from app.storage.local_storage import LocalImageStorage
from PIL import Image


@pytest.mark.unit
class TestImageService:
    @pytest.fixture
    def mock_repository(self):
        return Mock()

    @pytest.fixture
    def image_service(self, temp_directories, mock_repository, test_settings, format_extensions):
        storage = LocalImageStorage(
            directories=temp_directories,
            format_extensions=format_extensions,
        )
        return ImageService(
            settings=test_settings,
            repository=mock_repository,
            storage=storage,
        )

    def _make_record(self, filename: str, folder: str, path: Path, width: int = 100, height: int = 100):
        record = Mock()
        record.id = "test-id"
        record.filename = filename
        record.folder = folder
        record.path = str(path)
        record.format = "JPEG"
        record.mode = "RGB"
        record.width = width
        record.height = height
        record.size_bytes = 1024
        return record

    def test_get_folder_names(self):
        assert ImageFolder.get_folder_names("uploaded") == ["uploaded"]
        assert ImageFolder.get_folder_names("all") == ["uploaded", "edited", "detected"]

    def test_get_images_from_db(self, image_service, mock_repository):
        record = self._make_record("listed.jpg", "uploaded", Path("/tmp/listed.jpg"))
        mock_repository.get_by_folder.return_value = [record]

        results = image_service.get_images("uploaded", limit=10, offset=0)

        assert len(results) == 1
        assert isinstance(results[0], ImageDTO)
        assert results[0].filename == "listed.jpg"
        mock_repository.get_by_folder.assert_called_once_with(
            folders=["uploaded"], limit=10, offset=0
        )

    def test_get_images_all_folders(self, image_service, mock_repository):
        records = [
            self._make_record("a.jpg", "uploaded", Path("/tmp/a.jpg")),
            self._make_record("b.jpg", "edited", Path("/tmp/b.jpg")),
        ]
        mock_repository.get_by_folder.return_value = records

        results = image_service.get_images("all", limit=100, offset=0)

        assert len(results) == 2
        mock_repository.get_by_folder.assert_called_once_with(
            folders=["uploaded", "edited", "detected"], limit=100, offset=0
        )

    def test_get_image_path_from_db(self, image_service, mock_repository, temp_directories):
        image_path = temp_directories["uploaded"] / "db_test.jpg"
        Image.new("RGB", (100, 100), color="red").save(image_path, format="JPEG")

        record = self._make_record("db_test.jpg", "uploaded", image_path)
        mock_repository.get_by_filename.return_value = record

        assert image_service.get_image_path("db_test.jpg", "uploaded") == image_path

    def test_get_image_by_filename_from_db(self, image_service, mock_repository, temp_directories):
        image_path = temp_directories["uploaded"] / "db_meta.jpg"
        record = self._make_record("db_meta.jpg", "uploaded", image_path)
        mock_repository.get_by_filename.return_value = record

        result = image_service.get_image_by_filename("db_meta.jpg", "uploaded")

        assert isinstance(result, ImageDTO)
        assert result.filename == "db_meta.jpg"
        assert result.path == str(image_path)

    def test_get_image_by_filename_not_found(self, image_service, mock_repository):
        mock_repository.get_by_filename.return_value = None

        with pytest.raises(ImageNotFoundError):
            image_service.get_image_by_filename("nonexistent.jpg", "uploaded")

    def test_delete_image_uses_db_path(self, image_service, mock_repository, temp_directories):
        image_path = temp_directories["uploaded"] / "db_delete.jpg"
        Image.new("RGB", (100, 100), color="red").save(image_path, format="JPEG")

        record = self._make_record("db_delete.jpg", "uploaded", image_path)
        mock_repository.get_by_filename.return_value = record

        result = image_service.delete_image("db_delete.jpg", "uploaded")

        assert result.status == "success"
        assert not image_path.exists()
        mock_repository.delete_by_filename.assert_called_once_with("db_delete.jpg", "uploaded")

    def test_delete_image_not_found(self, image_service, mock_repository):
        mock_repository.get_by_filename.return_value = None

        with pytest.raises(ImageNotFoundError):
            image_service.delete_image("nonexistent.jpg", "uploaded")

    def test_delete_images_single_folder(self, image_service, mock_repository, temp_directories):
        records = []
        for index in range(5):
            image_path = temp_directories["uploaded"] / f"test_{index}.jpg"
            Image.new("RGB", (100, 100), color="blue").save(image_path, format="JPEG")
            records.append(self._make_record(f"test_{index}.jpg", "uploaded", image_path))

        mock_repository.get_all_by_folders.return_value = records

        result = image_service.delete_images("uploaded")

        assert result.status == "success"
        assert result.message == "Deleted 5 images from uploaded"
        assert len(list(temp_directories["uploaded"].glob("*.jpg"))) == 0

    def test_delete_images_all_folders(self, image_service, mock_repository, temp_directories):
        records = []
        for folder in ["uploaded", "edited", "detected"]:
            for index in range(2):
                image_path = temp_directories[folder] / f"test_{index}.jpg"
                Image.new("RGB", (100, 100), color="green").save(image_path, format="JPEG")
                records.append(self._make_record(f"test_{index}.jpg", folder, image_path))

        mock_repository.get_all_by_folders.return_value = records

        result = image_service.delete_images("all")

        assert result.status == "success"
        assert "Deleted" in result.message

    def test_delete_images_invalid_folder(self, image_service):
        with pytest.raises(InvalidFolderError):
            image_service.delete_images("invalid_folder")

    def test_move_image_updates_db(self, image_service, mock_repository, temp_directories):
        source_path = temp_directories["uploaded"] / "db_move.jpg"
        Image.new("RGB", (100, 100), color="red").save(source_path, format="JPEG")

        record = self._make_record("db_move.jpg", "uploaded", source_path)
        updated_image = ImageDTO(
            id="test-id",
            filename="db_move.jpg",
            format="JPEG",
            mode="RGB",
            width=100,
            height=100,
            size_bytes=1024,
            path=str(temp_directories["edited"] / "db_move.jpg"),
            folder="edited",
        )
        mock_repository.get_by_filename.return_value = record
        mock_repository.update.return_value = updated_image

        result = image_service.move_image("db_move.jpg", "uploaded", "edited")

        assert result.folder == "edited"
        assert not source_path.exists()
        assert (temp_directories["edited"] / "db_move.jpg").exists()

    def test_move_image_same_folders(self, image_service, temp_directories):
        image_path = temp_directories["uploaded"] / "test.jpg"
        Image.new("RGB", (100, 100), color="blue").save(image_path, format="JPEG")

        with pytest.raises(InvalidMoveError):
            image_service.move_image("test.jpg", "uploaded", "uploaded")

    def test_move_image_not_found(self, image_service, mock_repository):
        mock_repository.get_by_filename.return_value = None

        with pytest.raises(ImageNotFoundError):
            image_service.move_image("nonexistent.jpg", "uploaded", "edited")

    def test_move_image_target_exists(self, image_service, mock_repository, temp_directories):
        source_path = temp_directories["uploaded"] / "test.jpg"
        target_path = temp_directories["edited"] / "test.jpg"
        Image.new("RGB", (100, 100), color="red").save(source_path, format="JPEG")
        Image.new("RGB", (100, 100), color="red").save(target_path, format="JPEG")

        record = self._make_record("test.jpg", "uploaded", source_path)
        mock_repository.get_by_filename.return_value = record

        with pytest.raises(ImageConflictError):
            image_service.move_image("test.jpg", "uploaded", "edited")
