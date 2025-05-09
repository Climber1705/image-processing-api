from pathlib import Path
from typing import Dict, Optional
from fastapi import HTTPException, status, Depends
from app.core.logging_config import get_logger
from app.core.dependencies import get_directories

# Set up logger for FileFinder class
logger = get_logger("file_utils")

class FilePathResolver:
    """
    FilePathResolver class resolves file paths across provided directories.
    It locates files by name and validates their existence.
    """

    def __init__(self, directories: Dict[str, Path]):
        """
        Initializes the FileFinder with the directories to search for files.
        
        @param directories: A dictionary of directories to search for files (e.g., {"uploads": Path("/path/to/uploads")})
        """
        self.directories = directories
        logger.info("FileFinder initialized with directories: %s", self.directories)

    def _get_existing_file_path(self, filename: str) -> Optional[Path]:
        """
        Searches through all directories for the specified file.
        
        @param filename: The name of the file to search for.
        
        Returns the path to the file if found, otherwise returns None.
        """
        for directory in self.directories.values():
            file_path = directory / filename
            if file_path.is_file():
                logger.debug(f"File found: {file_path}")
                return file_path
        logger.debug(f"File not found: {filename}")
        return None

    def find_file(self, filename: str) -> Path:
        """
        Finds a file by its name in the provided directories.
        
        @param filename: The name of the file to search for.
        
        Raises an HTTPException if the file is not found.
        
        Returns the path to the file if found.
        """
        file_path = self._get_existing_file_path(filename)
        if not file_path:
            logger.warning(f"No file named '{filename}' exists in any of the directories")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No file named '{filename}' exists"
            )
        logger.info(f"File found: {file_path}")
        return file_path

    def find_and_validate_image(self, image_name: str) -> str:
        """
        Finds and validates the existence of an image file by name.
        
        @param image_name: The name of the image file to search for.
        
        Raises an HTTPException if the image is not found.
        
        Returns the path to the image if found.
        """
        image_path = self.find_file(image_name)
        if not image_path.exists():
            logger.warning(f"Image not found: {image_name}")
            raise HTTPException(status_code=404, detail="Image not found")
        logger.info(f"Image validated: {image_path}")
        return str(image_path)

def get_file_path_resolver(directories: Dict[str, Path] = Depends(get_directories)) -> FilePathResolver:
    """
    Dependency injection function to create an instance of FilePathResolver.
    
    @param directories: A dictionary of directories provided by the dependency system.
    
    Returns an instance of FilePathResolver.
    """
    logger.debug("Creating FilePathResolver instance with directories: %s", directories)
    return FilePathResolver(directories=directories)
