from fastapi import APIRouter

from app.api.routes.health import router as health_router
from app.api.routes.image import router as image_router
from app.api.routes.editing import router as editing_router
from app.api.routes.detection import router as detection_router

router = APIRouter()
router.include_router(health_router)
router.include_router(image_router)
router.include_router(editing_router)
router.include_router(detection_router)