# Core Module

## Overview

The `core` module provides foundational configuration, logging, rate limiting, and application lifespan management.

## Components

### `config.py` — Application Configuration

- **Settings**: Pydantic-settings class loaded from `.env`
- **Paths**: Uploaded, edited, and detected image directories
- **Inference**: Model name, device, confidence threshold, concurrency limits
- **setup()**: Creates required directories and database parent folder

No logging side effects — configuration is pure.

### `lifespan.py` — Application Lifecycle

- Initializes database on startup
- Loads and warms up the DETR inference engine
- Cleans up engine reference on shutdown

### `logging_config.py` — Logging

- Rotating file handler (`logs/app.log`, 5 MB × 5 backups)
- Optional console handler when `LOG_LEVEL=DEBUG`
- `get_logger(name)` factory for module-specific loggers

### `rate_limiting.py` — Rate Limiting

- Global slowapi limiter keyed on client IP
- Applied via `@limiter.limit()` on route handlers

## Usage

```python
from app.core.config import get_settings
from app.core.logging_config import get_logger

settings = get_settings()
logger = get_logger("my_module")
```

```python
from app.core.rate_limiting import limiter

@router.get("/endpoint")
@limiter.limit("10/minute")
async def limited_endpoint(request: Request):
    ...
```

## Related Documentation

- [Architecture Overview](../../docs/ARCHITECTURE.md)
- [ML Serving](../../docs/ML_SERVING.md)
