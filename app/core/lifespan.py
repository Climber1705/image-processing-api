import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import get_logger
from app.db.session import init_db
from app.vision.inference.engine import InferenceEngine

logger = get_logger("lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Initializing database")
    await asyncio.to_thread(init_db)

    logger.info("Starting inference engine load")
    app.state.inference_engine = InferenceEngine.from_settings(settings)

    if settings.WARMUP_ON_STARTUP:
        await asyncio.to_thread(app.state.inference_engine.warmup)
    else:
        app.state.inference_engine.mark_ready()

    logger.info("Inference engine ready")
    yield

    logger.info("Shutting down inference engine")
    app.state.inference_engine = None
