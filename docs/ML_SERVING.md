# ML Serving

This document describes how inference is served, concurrency limits, and how to run inference-related tests.

## Inference pipeline

All detection flows share one code path:

```
bytes or stored image → PIL.Image (RGB) → InferenceEngine.predict() → DTO
```

Optional flags on `InferenceService.detect()`:

- `visualize=True` — draw bounding boxes on the image
- `persist=True` — save annotated output to the `detected` media folder (requires `visualize=True`)

Stateless multipart detection is available at `POST /v1/inference/detect`. Visualization without persistence returns `annotated_image_base64` in the JSON response.

## Concurrency

Inference routes and legacy detection routes acquire a shared asyncio semaphore before running blocking work in a thread pool:

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

## Test tiers

| Tier | Command | When |
|------|---------|------|
| Fast (CI default) | `pytest -m "not inference"` | Every PR/push |
| Integration | `pytest tests/integration` | Local / CI |
| Real model (slow) | `pytest -m inference` | Manual / nightly |

Fast tests mock `InferenceEngine` and never download DETR weights.

### Running inference-marked tests locally

```bash
# Requires network on first run to download model weights; CPU recommended
pytest -m inference
```

Mark slow real-model tests with `@pytest.mark.inference` in test files. These are excluded from PR CI and the Docker build gate.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_CONCURRENT_INFERENCES` | `2` | Max parallel inference jobs |
| `INFERENCE_DEVICE` | `cpu` | Torch device (`cpu` or `cuda`) |
| `WARMUP_ON_STARTUP` | `true` | Run a dummy forward pass at startup |
| `CONFIDENCE_THRESHOLD` | `0.5` | Minimum detection score |
