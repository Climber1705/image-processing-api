#!/usr/bin/env python3
"""Measure DETR inference latency on CPU for docs/ML_SERVING.md."""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

# Allow running as `python scripts/benchmark_inference.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image

from app.core.config import get_settings
from app.vision.inference.engine import InferenceEngine


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    index = max(0, min(len(sorted_values) - 1, int(len(sorted_values) * pct) - 1))
    return sorted_values[index]


def benchmark_size(
    engine: InferenceEngine,
    image_size: tuple[int, int],
    *,
    confidence_threshold: float,
    runs: int,
    warmup_runs: int,
) -> dict[str, float | int]:
    image = Image.new("RGB", image_size, color=(100, 150, 200))

    for _ in range(warmup_runs):
        engine.predict(image, confidence_threshold)

    durations_ms: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        engine.predict(image, confidence_threshold)
        durations_ms.append((time.perf_counter() - start) * 1000)

    durations_ms.sort()
    return {
        "width": image_size[0],
        "height": image_size[1],
        "runs": runs,
        "p50_ms": statistics.median(durations_ms),
        "p95_ms": _percentile(durations_ms, 0.95),
        "min_ms": durations_ms[0],
        "max_ms": durations_ms[-1],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark DETR inference latency.")
    parser.add_argument("--runs", type=int, default=5, help="Timed runs per image size.")
    parser.add_argument("--warmup", type=int, default=1, help="Warmup runs per image size.")
    args = parser.parse_args()

    settings = get_settings()
    print(f"Loading model {settings.MODEL_NAME} on {settings.INFERENCE_DEVICE}...")
    engine = InferenceEngine.from_settings(settings)
    engine.warmup()

    sizes = [(640, 480), (1333, 1000)]
    print(f"Benchmarking {args.runs} runs per size (warmup={args.warmup})...\n")

    for size in sizes:
        result = benchmark_size(
            engine,
            size,
            confidence_threshold=settings.CONFIDENCE_THRESHOLD,
            runs=args.runs,
            warmup_runs=args.warmup,
        )
        print(
            f"{result['width']}x{result['height']}: "
            f"p50={result['p50_ms']:.0f} ms  "
            f"p95={result['p95_ms']:.0f} ms  "
            f"min={result['min_ms']:.0f} ms  "
            f"max={result['max_ms']:.0f} ms"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
