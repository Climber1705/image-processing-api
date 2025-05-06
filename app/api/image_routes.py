from fastapi import APIRouter, UploadFile, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict

from app.services.file_io.file_controller import FileController
from app.core.dependencies import get_file_controller

router = APIRouter(
    prefix="/api/images",
    tags=["Images"],
    responses={404: {"description": "Not found"}},
)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile,
    filename: Optional[str] = None,
    format: str = "JPEG",
    controller: FileController = Depends(get_file_controller),
) -> Dict:
    """Upload an image file"""
    try:
        file_path = controller.save_uploaded_image(file, filename, format)
        return {
            "status": "success",
            "path": file_path,
            "metadata": controller.get_image_metadata(file_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )

@router.get("", response_model=List[Dict])
async def get_images(
    folder: str = Query("all", description="Folder to list (uploads, processed, analyzed, all)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    controller: FileController = Depends(get_file_controller),
) -> List[Dict]:
    """List images with pagination"""
    try:
        return controller.list_images(folder, limit, offset)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list images: {str(e)}"
        )

@router.get("/{image_id}", response_model=Dict)
async def get_image(
    image_id: str,
    folder: str = Query("uploads", description="Folder containing the image"),
    controller: FileController = Depends(get_file_controller),
) -> Dict:
    """Get image details and metadata"""
    try:
        return controller.get_image_by_id(image_id, folder)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image: {str(e)}"
        )

@router.get("/{image_id}/dimensions", response_model=Dict)
async def get_dimensions(
    image_id: str,
    folder: str = Query("uploads", description="Folder containing the image"),
    controller: FileController = Depends(get_file_controller),
) -> Dict:
    """Get image dimensions"""
    try:
        image_path = controller.get_image_path(image_id, folder)
        width, height = controller.get_image_dimensions(image_path)
        return {"width": width, "height": height}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dimensions: {str(e)}"
        )

@router.delete("/{image_id}", status_code=status.HTTP_200_OK)
async def delete_image(
    image_id: str,
    folder: str = Query("uploads", description="Folder containing the image"),
    controller: FileController = Depends(get_file_controller),
) -> Dict:
    """Delete an image"""
    try:
        return controller.delete_image(image_id, folder)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete image: {str(e)}"
        )

@router.post("/{image_id}/move", status_code=status.HTTP_200_OK)
async def move_image(
    image_id: str,
    source_folder: str = Query(..., description="Current folder of the image"),
    target_folder: str = Query(..., description="Destination folder for the image"),
    controller: FileController = Depends(get_file_controller),
) -> Dict:
    """Move image between folders"""
    try:
        return controller.move_image(image_id, source_folder, target_folder)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move image: {str(e)}"
        )

@router.delete("", status_code=status.HTTP_200_OK)
async def clear_images(
    folder: str = Query("all", description="Folder to clear (uploads, processed, analyzed, all)"),
    controller: FileController = Depends(get_file_controller),
) -> Dict:
    """Delete all images in specified folder(s)"""
    try:
        return controller.delete_all_images(folder)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear folder: {str(e)}"
        )