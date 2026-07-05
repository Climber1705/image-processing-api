# ML Serving

This document describes how inference is served, concurrency limits, and how to run inference-related tests.

## Inference pipeline

All detection flows share one code path:

```
bytes or stored image → image_loader (PIL RGB) → InferenceEngine.predict() → DetectResponseDTO → Pydantic response
```

Optional flags on `InferenceService.detect()`:

- `visualize=True` — draw bounding boxes on the image
- `persist=True` — save annotated output to the `detected` media folder (requires `visualize=True`)

Stateless multipart detection is available at `POST /v1/inference/detect`. Visualization without persistence returns `annotated_image_base64` in the JSON response.

## Module layout

| Module | Purpose |
|--------|---------|
| `vision/image_loader.py` | PIL verify, dimension check, RGB conversion |
| `vision/inference/engine.py` | Model load, warmup, predict |
| `vision/inference/preprocessor.py` | Resize + tensor prep |
| `vision/inference/postprocessor.py` | HF post-process + map to DTOs |
| `vision/inference/visualizer.py` | Bounding-box drawing |
| `vision/service.py` | Orchestration: validate → predict → visualize/persist |
| `dependencies/inference.py` | Semaphore + thread-pool gate |

## Concurrency

Inference routes acquire a shared asyncio semaphore before running blocking work in a thread pool:

- Setting: `MAX_CONCURRENT_INFERENCES` (default: `2`)
- Dependency: `app/dependencies/inference.py` → `run_inference()`

Editing routes do not use this semaphore.

Rationale: `InferenceEngine.predict()` is synchronous and uses PIL/torch. `asyncio.to_thread()` offloads blocking work without blocking the event loop, while the semaphore caps how many inferences run concurrently.

## API surface

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/inference/detect` | Stateless or by-reference detection (metadata only) |
| `POST /v1/inference/detect/visualize` | Detection + optional visualization/persistence |
| `GET /v1/inference/models` | Loaded model metadata and readiness |

### Input modes

Both detect endpoints accept either:

- **Multipart file** — `file` form field with an image upload
- **Stored image reference** — `image_name` + optional `folder` query params

## Startup and readiness

On boot (`app/core/lifespan.py`):

1. Initialize database
2. Load DETR model from Hugging Face
3. Run warmup forward pass (if `WARMUP_ON_STARTUP=true`)

`GET /health/ready` returns 503 until warmup completes and storage directories are writable.

## Test tiers

| Tier | Command | When |
|------|---------|------|
| Fast (CI default) | `pytest -m "not inference"` | Every PR/push |
| Integration | `pytest tests/integration` | Local / CI |
| Real model (slow) | `pytest -m inference --no-cov` | Manual / nightly (`.github/workflows/test-inference.yml`) |

Fast tests mock `InferenceEngine` and never download DETR weights.

Smoke tests in `tests/inference/test_detr_smoke.py` cover:

- Direct `InferenceEngine.predict()` (640×480 and large-input resize path)
- `POST /v1/inference/detect` over HTTP with a real warmed-up model
- `GET /health/ready` after model load

### Running inference-marked tests locally

```bash
# Requires network on first run to download model weights; CPU recommended
pytest -m inference --no-cov
```

Mark slow real-model tests with `@pytest.mark.inference`. These are excluded from PR CI and the Docker build gate.

## CPU latency (measured)

Benchmarks from `scripts/benchmark_inference.py` on **CPU** (`INFERENCE_DEVICE=cpu`), model `facebook/detr-resnet-50`, 5 timed runs per size after 1 warmup run (measured 2026-07-05 on Linux):

| Input size | p50 | p95 | Notes |
|------------|-----|-----|-------|
| 640×480 | ~3.8 s | ~3.8 s | Typical upload size |
| 1333×1000 | ~3.5 s | ~3.5 s | Downscaled to `MAX_IMAGE_DIMENSION` (1333) before inference |

Reproduce:

```bash
python scripts/benchmark_inference.py --runs 5 --warmup 1
```

First run downloads Hugging Face weights; subsequent runs reflect steady-state inference only. GPU would lower these numbers but is not benchmarked in-repo.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_INFERENCES` | `2` | Max parallel inference jobs |
| `INFERENCE_DEVICE` | `cpu` | Torch device (`cpu` or `cuda`) |
| `WARMUP_ON_STARTUP` | `true` | Run a dummy forward pass at startup |
| `CONFIDENCE_THRESHOLD` | `0.5` | Minimum detection score |
| `MAX_IMAGE_DIMENSION` | `1333` | Max pixel dimension before resize |
| `MODEL_NAME` | `facebook/detr-resnet-50` | Hugging Face model ID |
