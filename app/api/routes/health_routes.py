from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["System"])


@router.get("/")
async def root():
    return JSONResponse(
        status_code=200,
        content={"message": "Welcome to the Image Processing API"},
    )


@router.get("/health")
async def health():
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "Image Processing API",
            "version": "1.0.0",
        },
    )
