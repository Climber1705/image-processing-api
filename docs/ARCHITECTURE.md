# Architecture Overview

[← Back to Main README](../README.md)

System architecture, design patterns, and technical details of the Image Processing API.

## Architecture Pattern

The API uses **bounded contexts** with a shared infrastructure layer:

```
┌─────────────────────────────────────────────────────────┐
│  API Routes (app/api/routes/)                           │
│  HTTP adapters — validate input, map responses          │
├──────────────┬──────────────────┬───────────────────────┤
│  media/      │  editing/        │  vision/              │
│  api/        │  api/            │  api/                 │
│  domain/     │  domain/         │  domain/              │
│  service.py  │  service.py      │  service.py           │
│              │                  │  inference/ (engine)  │
├──────────────┴──────────────────┴───────────────────────┤
│  Infrastructure: core/, dependencies/, storage/, db/    │
└─────────────────────────────────────────────────────────┘
```

Each bounded context follows the same internal layout:

| Layer | Responsibility |
|-------|----------------|
| `api/` | Pydantic request/response models, mappers, exception handlers |
| `domain/` | DTOs and domain exceptions (no FastAPI or ORM imports) |
| `service.py` | Orchestration — coordinates domain logic and infrastructure |
| `inference/` (vision only) | ML pipeline: preprocess → model → postprocess |

## Module Organization

```
app/
├── api/routes/          health.py, image.py, editing.py, inference.py
├── core/                config, lifespan, logging, rate limiting
├── dependencies/        FastAPI DI factories
├── media/               image upload, list, delete, move
├── editing/             Pillow transforms
├── vision/              object detection
│   ├── api/             inputs, mappers, responses, handlers
│   ├── domain/          DTOs, errors
│   ├── inference/       engine, pre/postprocessor, visualizer
│   ├── image_loader.py  PIL validation (shared by service)
│   └── service.py       InferenceService
├── storage/             BaseImageStorage, LocalImageStorage
├── db/                  SQLAlchemy session and models
└── validation/          upload type/size validation
```

## Request Flow: Object Detection

```
POST /v1/inference/detect
  → resolve_image_bytes()          # multipart file or stored image reference
  → run_inference()                # semaphore + asyncio.to_thread
  → InferenceService.detect()
      → load_from_bytes()          # PIL verify + RGB conversion
      → InferenceEngine.predict()  # DETR forward pass
      → to_detect_response_dto() # domain DTO
  → to_inference_detect_response() # Pydantic response
```

Visualization adds `draw_bounding_boxes()` and optional persistence to the `detected` folder.

## AI Model: DETR

This project uses **DEtection TRansformer (DETR)** (`facebook/detr-resnet-50`) for object detection.

| Component | Role |
|-----------|------|
| `DetrImageProcessor` | Resize, normalize, tensor conversion |
| `DetrForObjectDetection` | Forward pass — bounding boxes + class scores |
| `postprocessor.py` | HF `post_process_object_detection` with confidence threshold |
| `visualizer.py` | Draw boxes and labels with Pillow |

The model loads at application startup (`app/core/lifespan.py`). Weights are cached by Hugging Face after the first download (~500 MB).

## Performance & Concurrency

- All route handlers are `async def`.
- Blocking work (file I/O, Pillow, PyTorch) runs via `asyncio.to_thread()`.
- Inference routes acquire a shared semaphore (`MAX_CONCURRENT_INFERENCES`, default 2) before entering the thread pool.
- Readiness probe at `/health/ready` checks model warmup, storage writability, and engine initialization.

## Design Patterns

### Dependency Injection

Services receive dependencies through constructors. FastAPI `Depends()` factories in `app/dependencies/` wire everything at request time.

### Domain Exceptions

Each bounded context defines its own exception hierarchy (`MediaDomainError`, `VisionDomainError`, etc.) with registered FastAPI exception handlers that map to HTTP status codes.

### Data Transfer Objects

- **Domain DTOs** — frozen dataclasses in `domain/dtos.py` (service layer)
- **API responses** — Pydantic models in `api/responses.py` (HTTP layer)
- **Inference internals** — `DetectionResult` and `EngineMetadata` in `vision/inference/schemas.py`

Detection data flows: raw tensors → `DetectionDTO` → Pydantic `DetectionBox`. Two layers, not three.

## Storage Architecture

| Folder | Path | Purpose |
|--------|------|---------|
| uploaded | `app/static/uploaded/` | Original uploads |
| edited | `app/static/edited/` | Transformed images |
| detected | `app/static/detected/` | Annotated detection outputs |

Storage is abstracted through `BaseImageStorage`; `LocalImageStorage` is the current implementation.

## Logging & Monitoring

- Rotating file log: `logs/app.log` (configured in `app/core/logging_config.py`)
- Liveness: `GET /health/live`
- Readiness: `GET /health/ready` (model + storage checks)
- Rate limiting: slowapi per-endpoint limits

## Related Documentation

- [ML Serving](ML_SERVING.md) — inference pipeline, concurrency, test tiers
- [API Documentation](API.md) — endpoint reference
- [Development Guide](DEVELOPMENT.md) — testing and conventions
- [Deployment Guide](DEPLOYMENT.md) — production setup

---

[← Back to Main README](../README.md) | [Documentation Index](README.md)
