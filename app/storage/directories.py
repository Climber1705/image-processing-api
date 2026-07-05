from pathlib import Path

from fastapi import HTTPException, status

from app.core.logging_config import get_logger

logger = get_logger("directories")


class DirectoryManager:
    def __init__(self, directories: dict[str, Path]):
        self.directories = directories
        logger.info("Initializing DirectoryManager with directories: %s", self.directories)
        self._create_directories()

    def _create_directories(self) -> None:
        for directory in self.directories.values():
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create directory: {directory}. Error: {e}",
                )

    def validate_folder(self, folder: str) -> bool:
        is_valid = folder in self.directories
        logger.debug(f"Validating folder '{folder}': {'Valid' if is_valid else 'Invalid'}")
        return is_valid

    def get_directory(self, folder: str) -> Path:
        if not self.validate_folder(folder):
            logger.warning(f"Invalid folder requested: {folder}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid folder: {folder}",
            )
        logger.info(f"Returning directory path for folder: {folder}")
        return self.directories[folder]
