# Routes Module

## Overview

FastAPI endpoint definitions organized by bounded context. Each route file is a thin HTTP adapter that delegates to services via dependency injection.

## Route Files

| File | Prefix | Purpose |
|------|--------|---------|
| `health.py` | `/` | Liveness and readiness probes |
| `image.py` | `/images` | Upload, list, get, delete, move |
| `editing.py` | `/images/{filename}/edits` | Pillow transformations |
| `inference.py` | `/v1/inference` | Object detection (DETR) |

Routes are aggregated in `app/api/routes/__init__.py` and mounted from `app/main.py`.

## Patterns

### Dependency injection

```python
@router.post("/detect")
async def detect(service: InferenceService = Depends(get_inference_service)):
    ...
```

### Async + thread pool for blocking work

```python
result = await run_inference(lambda: service.detect(image_bytes))
```

Inference routes use `run_inference()` (semaphore + `asyncio.to_thread`). Editing routes wrap Pillow operations similarly.

### Rate limiting

Applied via `@limiter.limit("N/minute")` on each endpoint. System/health routes are unbounded.

### Domain exceptions

Routes raise domain errors (`VisionDomainError`, `MediaDomainError`, etc.) registered in `main.py`. Vision input validation uses `InvalidInputError` → 400.

## Related Documentation

- [API Module README](../README.md)
- [Architecture Overview](../../../docs/ARCHITECTURE.md)
- [ML Serving](../../../docs/ML_SERVING.md)
