
from pathlib import Path
from app.core.logging_config import get_logger
import shutil

logger = get_logger("clean_up")

def clean_up(directory: Path) -> None:
    #Recursively removes __pycache__ directories.
    for pycache in directory.rglob('__pycache__'):
        if pycache.is_dir():
            try:
                shutil.rmtree(pycache)
                logger.info(f"Successfully removed {pycache}")
            except Exception as e:
                logger.error(f"Failed to remove {pycache}: {e}")
