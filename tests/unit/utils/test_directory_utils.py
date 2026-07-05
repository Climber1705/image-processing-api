"""
Unit tests for DirectoryManager utility.
"""

import pytest
from fastapi import HTTPException

from app.storage.directories import DirectoryManager


@pytest.mark.unit
class TestDirectoryManager:
    """Test cases for DirectoryManager."""

    @pytest.fixture
    def directory_manager(self, temp_directories):
        """Create DirectoryManager with test directories."""
        return DirectoryManager(directories=temp_directories)

    def test_validate_folder_valid(self, directory_manager):
        """Test validating valid folder names."""
        valid_folders = ["uploaded", "edited", "detected"]
        
        for folder in valid_folders:
            assert directory_manager.validate_folder(folder) is True

    def test_validate_folder_invalid(self, directory_manager):
        """Test validating invalid folder names."""
        invalid_folders = ["invalid", "nonexistent", "random"]
        
        for folder in invalid_folders:
            assert directory_manager.validate_folder(folder) is False

    def test_get_directory_success(self, directory_manager, temp_directories):
        """Test getting directory path successfully."""
        result = directory_manager.get_directory("uploaded")
        
        assert result == temp_directories["uploaded"]

    def test_get_directory_invalid_folder(self, directory_manager):
        """Test getting directory with invalid folder name."""
        with pytest.raises(HTTPException) as exc_info:
            directory_manager.get_directory("invalid_folder")
        
        assert exc_info.value.status_code == 400
        assert "Invalid folder" in exc_info.value.detail

    def test_create_directories_auto_creation(self, temp_base_dir):
        """Test automatic directory creation."""
        new_dirs = {
            "test1": temp_base_dir / "new_test1",
            "test2": temp_base_dir / "new_test2"
        }
        
        manager = DirectoryManager(directories=new_dirs)
        
        assert new_dirs["test1"].exists()
        assert new_dirs["test2"].exists()

    def test_create_directories_existing(self, directory_manager, temp_directories):
        """Test directory creation when directories already exist."""
        assert temp_directories["uploaded"].exists()
        assert temp_directories["edited"].exists()
        assert temp_directories["detected"].exists()



