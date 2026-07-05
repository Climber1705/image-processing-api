from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.storage.directories import storage_dirs_writable


router = APIRouter(tags=["System"])

@router.get("/")
async def root():
    return JSONResponse(
        status_code=200,
        content={"message": "Welcome to the Image Processing API"},
    )


@router.get("/health/live")
async def health_live():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "Image Processing API",
            "version": "1.0.0",
        },
    )


@router.get("/health/ready")
async def health_ready(request: Request):
    engine = getattr(request.app.state, "inference_engine", None)
    checks = {
        "model_loaded": engine is not None,
        "warmup_complete": engine is not None and engine.is_ready,
        "storage_writable": storage_dirs_writable(settings.directories.values()),
    }
    ready = all(checks.values())

    content = {
        "status": "ready" if ready else "not_ready",
        "checks": checks,
    }
    if engine is not None:
        content["model_name"] = engine.metadata.model_name
        content["model_version"] = engine.metadata.model_revision

    return JSONResponse(status_code=200 if ready else 503, content=content)
