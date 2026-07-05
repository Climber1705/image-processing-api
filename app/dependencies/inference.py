import asyncio
from typing import TypeVar
from collections.abc import Callable

from app.core.config import settings

T = TypeVar("T")


async def run_inference(func: Callable[[], T]) -> T:
    async with asyncio.Semaphore(settings.MAX_CONCURRENT_INFERENCES):
        return await asyncio.to_thread(func)
