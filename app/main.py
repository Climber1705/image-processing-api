from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import detection_routes, image_routes, editing_routes, health_routes
from app.core.rate_limiting import limiter
from app.utils.system.lifespan import lifespan

description = """
Upload, manage, and process images.

Images are stored in **uploaded**, **edited**, and **detected** folders.
Supports Pillow transformations and object detection via DETR.
"""

app = FastAPI(
    title="Image Processing API",
    description=description,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(image_routes.router)
app.include_router(editing_routes.router)
app.include_router(detection_routes.router)
app.include_router(health_routes.router)
