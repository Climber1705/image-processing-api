# API Module

## Overview

The `api` module contains all FastAPI route definitions. Routes are thin HTTP adapters that delegate to bounded-context services.

## Architecture

```
Client Request
    ↓
api/routes/          (HTTP adapters)
    ↓
dependencies/        (FastAPI DI)
    ↓
media/ | editing/ | vision/   (services)
```

## Route Files

- **`routes/health.py`** — `/`, `/health/live`, `/health/ready`
- **`routes/image.py`** — Image CRUD (`/images`)
- **`routes/editing.py`** — Pillow transforms (`/images/{filename}/edits`)
- **`routes/inference.py`** — DETR detection (`/v1/inference`)

## Usage

Routes are registered in `app/main.py`:

```python
from app.api.routes import router

app.include_router(router)
```

## Related Documentation

- [Routes README](routes/README.md)
- [Architecture Overview](../../docs/ARCHITECTURE.md)
