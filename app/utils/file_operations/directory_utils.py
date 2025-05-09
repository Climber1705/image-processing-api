from typing import Dict
from pathlib import Path
from fastapi import HTTPException, status, Depends
from app.core.logging_config import get_logger
from app.core.dependencies import get_directories


logger = get_logger("directory_utils")

class DirectoryManager:
    """
    DirectoryManager is responsible for managing and validating directories.
    It can create required directories and validate folder paths.
    """

    def __init__(self, directories: Dict[str, Path]):
        """
        Initializes the DirectoryManager with the provided directories.
        
        @param directories: A dictionary mapping folder names to directory paths (e.g., {"uploads": Path("/path/to/uploads")})
        """
        self.directories = directories
        logger.info("Initializing DirectoryManager with directories: %s", self.directories)

        self._create_directories()

    def _create_directories(self) -> None:
        """
        Creates directories defined in the `directories` attribute if they don't already exist.
        """
        for directory in self.directories.values():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}") 
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create directory: {directory}. Error: {e}"
                )

    def validate_folder(self, folder: str) -> bool:
        """
        Validates if a folder name exists in the `directories` attribute.
        
        @param folder: The folder name to validate.
        
        Returns True if the folder exists in `directories`, False otherwise.
        """
        is_valid = folder in self.directories
        logger.debug(f"Validating folder '{folder}': {'Valid' if is_valid else 'Invalid'}")
        return is_valid

    def get_directory(self, folder: str) -> Path:
        """
        Retrieves the directory path for a specified folder.
        
        @param folder: The folder name whose directory path needs to be retrieved.
        
        Returns the Path of the folder if valid, otherwise raises an HTTPException.
        """
        if not self.validate_folder(folder):
            logger.warning(f"Invalid folder requested: {folder}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid folder: {folder}"
            )
        logger.info(f"Returning directory path for folder: {folder}")
        return self.directories[folder]


def get_directory_manager(directories: Dict[str, Path] = Depends(get_directories)) -> DirectoryManager:
    """
    Dependency injection function to get an instance of DirectoryManager.
    
    @param directories: A dictionary of directories provided by the dependency system.
    
    Returns an instance of DirectoryManager.
    """
    logger.debug("Creating DirectoryManager instance with directories: %s", directories)
    return DirectoryManager(directories=directories)
