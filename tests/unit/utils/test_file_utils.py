"""
Unit tests for FilePathResolver utility.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from app.media.utils.file_utils import FilePathResolver


@pytest.mark.unit
class TestFilePathResolver:
    """Test cases for FilePathResolver."""

    @pytest.fixture
    def file_resolver(self, temp_directories):
        """Create FilePathResolver with test directories."""
        return FilePathResolver(directories=temp_directories)

    def test_find_file_success(self, file_resolver, temp_directories):
        """Test finding file successfully."""
        test_file = temp_directories["uploaded"] / "test_find.jpg"
        test_file.touch()
        
        result = file_resolver.find_file("test_find.jpg")
        
        assert result == test_file

    def test_find_file_in_different_directories(self, file_resolver, temp_directories):
        """Test finding file in different directories."""
        files = {
            "uploaded": temp_directories["uploaded"] / "test.jpg",
            "edited": temp_directories["edited"] / "test.jpg",
            "detected": temp_directories["detected"] / "test.jpg"
        }
        
        for folder, file_path in files.items():
            file_path.touch()
            result = file_resolver.find_file("test.jpg")
            assert result.exists()

    def test_find_file_not_found(self, file_resolver):
        """Test finding non-existent file."""
        with pytest.raises(HTTPException) as exc_info:
            file_resolver.find_file("nonexistent.jpg")
        
        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail.lower() or "does not exist" in exc_info.value.detail.lower()

    def test_find_and_validate_image_success(self, file_resolver, temp_directories):
        """Test finding and validating existing image."""
        test_file = temp_directories["uploaded"] / "test_validate.jpg"
        test_file.touch()
        
        result = file_resolver.find_and_validate_image("test_validate.jpg")
        
        assert result == str(test_file)

    def test_find_and_validate_image_not_found(self, file_resolver):
        """Test finding and validating non-existent image."""
        with pytest.raises(HTTPException) as exc_info:
            file_resolver.find_and_validate_image("nonexistent.jpg")
        
        assert exc_info.value.status_code == 404

    def test_get_existing_file_path_success(self, file_resolver, temp_directories):
        """Test internal method for finding existing file path."""
        test_file = temp_directories["edited"] / "test_internal.jpg"
        test_file.touch()
        
        result = file_resolver._get_existing_file_path("test_internal.jpg")
        
        assert result == test_file

    def test_get_existing_file_path_not_found(self, file_resolver):
        """Test internal method when file doesn't exist."""
        result = file_resolver._get_existing_file_path("nonexistent.jpg")
        
        assert result is None

    def test_find_file_resolves_from_db(self, temp_directories):
        """Test finding file via database path lookup."""
        mock_repo = Mock()
        test_file = temp_directories["uploaded"] / "db_resolved.jpg"
        test_file.touch()

        mock_record = Mock()
        mock_record.path = str(test_file)
        mock_repo.get_by_filename_any_folder.return_value = mock_record

        resolver = FilePathResolver(directories=temp_directories, image_repository=mock_repo)
        result = resolver.find_file("db_resolved.jpg")

        assert result == test_file
        mock_repo.get_by_filename_any_folder.assert_called_once_with("db_resolved.jpg")