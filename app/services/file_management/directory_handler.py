from typing import Dict
from pathlib import Path
import logging
from fastapi import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("file_handler")


class DirectoryHandler:
    """
    Manages creation and validation of directories for image storage.
    """
    
    def __init__(self, directories: Dict[str, Path]):
        self.directories = directories
        self._create_directories()
    
    def _create_directories(self) -> None:
        """
        Create the necessary directories if they don't exist.
        """
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def validate_folder(self, folder: str) -> bool:
        """
        Check if a folder exists in the known directories.
        
        Args:
            folder: Folder name to validate
            
        Returns:
            True if folder exists, False otherwise
        """
        return folder in self.directories
    
    def get_directory(self, folder: str) -> Path:
        """
        Get the Path object for a folder.
        
        Args:
            folder: Folder name
            
        Returns:
            Path object for the folder
            
        Raises:
            HTTPException: If folder is invalid
        """
        if not self.validate_folder(folder):
            raise HTTPException(status_code=400, detail=f"Invalid folder: {folder}")
        return self.directories[folder]