"""Unit tests for inference concurrency gating."""

import asyncio
import threading

import pytest
from app.dependencies.inference import (
    get_inference_semaphore,
    reset_inference_semaphore,
    run_inference,
)


@pytest.mark.unit
def test_get_inference_semaphore_returns_singleton():
    reset_inference_semaphore()
    first = get_inference_semaphore()
    second = get_inference_semaphore()
    assert first is second
    reset_inference_semaphore()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_run_inference_limits_parallelism(monkeypatch):
    """Concurrent run_inference calls respect MAX_CONCURRENT_INFERENCES."""
    monkeypatch.setattr("app.dependencies.inference.settings.MAX_CONCURRENT_INFERENCES", 1)
    reset_inference_semaphore()

    lock = threading.Lock()
    current = 0
    max_concurrent = 0
    hold = threading.Event()
    hold.clear()

    def blocking_work() -> None:
        nonlocal current, max_concurrent
        with lock:
            current += 1
            max_concurrent = max(max_concurrent, current)
        hold.wait(timeout=5)
        with lock:
            current -= 1

    tasks = [asyncio.create_task(run_inference(blocking_work)) for _ in range(3)]
    await asyncio.sleep(0.1)
    hold.set()
    await asyncio.gather(*tasks)

    assert max_concurrent == 1
    reset_inference_semaphore()
