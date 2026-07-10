import asyncio
from collections.abc import Callable

from app.core.config import settings

_inference_semaphore: asyncio.Semaphore | None = None


def get_inference_semaphore() -> asyncio.Semaphore:
    global _inference_semaphore
    if _inference_semaphore is None:
        _inference_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_INFERENCES)
    return _inference_semaphore


def reset_inference_semaphore() -> None:
    """Reset the module semaphore (for tests)."""
    global _inference_semaphore
    _inference_semaphore = None


async def run_inference[T](func: Callable[[], T]) -> T:
    async with get_inference_semaphore():
        return await asyncio.to_thread(func)
