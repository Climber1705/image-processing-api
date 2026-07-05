import asyncio
from collections.abc import Callable
from typing import TypeVar

from app.core.config import settings

_inference_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_INFERENCES)

T = TypeVar("T")


async def run_inference(func: Callable[[], T]) -> T:
    async with _inference_semaphore:
        return await asyncio.to_thread(func)
