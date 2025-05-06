from fastapi import FastAPI
from app.api import image_routes, processing_routes

app = FastAPI()

app.include_router(image_routes.router)
app.include_router(processing_routes.router)
#app.include_router(predict_image.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {"status": "OK", "message": "Favicon not found"}

@app.get("/")
async def root():
    return {"status": "OK", "message": "Image Processing API is running"}