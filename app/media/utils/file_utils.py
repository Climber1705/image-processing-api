from pathlib import Path
from fastapi import HTTPException, status

from app.core.logging_config import get_logger

logger = get_logger("file_utils")


class FilePathResolver:
    
    def __init__(self, directories: dict[str, Path]):
        self.directories = directories
        logger.info("FileFinder initialized with directories: %s", self.directories)

    def _get_existing_file_path(self, filename: str) -> Path | None:
        for directory in self.directories.values():
            file_path = directory / filename
            if file_path.is_file():
                logger.debug(f"File found: {file_path}")
                return file_path
        logger.debug(f"File not found: {filename}")
        return None

    def find_file(self, filename: str) -> Path:
        file_path = self._get_existing_file_path(filename)
        if not file_path:
            logger.warning(f"No file named '{filename}' exists in any of the directories")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' not found or does not exist",
            )
        logger.info(f"File found: {file_path}")
        return file_path

    def find_and_validate_image(self, image_name: str) -> str:
        try:
            image_path = self.find_file(image_name)
            if not image_path.exists():
                logger.warning(f"Image not found: {image_name}")
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
            logger.info(f"Image validated: {image_path}")
            return str(image_path)
        except HTTPException as e:
            if e.status_code == status.HTTP_400_BAD_REQUEST:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Image '{image_name}' not found",
                )
            raise
