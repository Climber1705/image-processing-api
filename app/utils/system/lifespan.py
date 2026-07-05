from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio

from app.utils.system.clean_up import clean_up
from app.core.logging_config import get_logger

logger = get_logger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting lifespan context...")

    project_root = Path(__file__).parent.parent.parent

    yield

    logger.info("Removing __pycache__ after shutdown...")
    await asyncio.to_thread(clean_up, project_root)
    logger.info("Lifespan context ended.")
