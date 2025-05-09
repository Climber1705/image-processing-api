from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
from app.utils.system.clean_up import clean_up
from app.core.logging_config import get_logger

logger = get_logger("lifespab")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles cleanup of pycache before startup and after shutdown."""
    logger.info("Starting lifespan context...")

    project_root = Path(__file__).parent.parent.parent
    
    yield 

    logger.info("Removing __pycache__ after shutdown...")
    clean_up(project_root)
    logger.info("Lifespan context ended.")
