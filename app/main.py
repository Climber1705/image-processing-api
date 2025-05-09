
from fastapi import FastAPI
from app.api.routes import detection_routes, image_routes, editing_routes
from app.utils.system.lifespan import lifespan

description = """
This API allows users to upload, manage, and process images.

## The following directories are used:
By default, images are stored in the following folders:
1. **uploaded** - Folder for uploaded images.
2. **edited** - Folder for edited images.
3. **detected** - Folder for detected image outputs.
"""

app = FastAPI(
    title="Image Processing API",
    description=description,
    lifespan=lifespan
)

app.include_router(image_routes.router)
app.include_router(editing_routes.router)
app.include_router(detection_routes.router)



