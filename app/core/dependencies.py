
from typing import Dict
from fastapi import Depends
from app.core.settings import settings

from app.services.file_io.directory_manager import DirectoryManager
from app.services.file_io.file_controller import FileController
from app.services.file_io.storage import ImageStorage
from app.services.file_io.file_operations import ImageOperation
from app.services.file_io.file_query import ImageQuery
from app.services.file_io.image_validator import ImageValidator

from app.services.processing.metadata import ImageMetadata
from app.services.processing.processing_controller import ImageProcessing

def get_folders():
    """Dependency to provide folder configuration"""
    return {
        "uploads": settings.UPLOAD_FOLDER,
        "processed": settings.PROCESSED_FOLDER,
        "analyzed": settings.ANALYZED_FOLDER,
    }


def get_image_validator():
    """Dependency for image validator service"""
    return ImageValidator()


def get_directory_manager(folders: Dict[str, str] = Depends(get_folders)):
    """Dependency for directory manager service"""
    return DirectoryManager(folders)


def get_metadata_service():
    """Dependency for metadata service"""
    return ImageMetadata()


def get_storage_service(
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    image_validator: ImageValidator = Depends(get_image_validator)
):
    """Dependency for storage service"""
    return ImageStorage(directory_manager, image_validator)


def get_operation_service(
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    metadata_service: ImageMetadata = Depends(get_metadata_service)
):
    """Dependency for file operations service"""
    return ImageOperation(directory_manager, metadata_service)


def get_query_service(
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    metadata_service: ImageMetadata = Depends(get_metadata_service)
):
    """Dependency for file query service"""
    return ImageQuery(directory_manager, metadata_service)

def get_file_controller(
    directory_manager: DirectoryManager = Depends(get_directory_manager),
    image_validator: ImageValidator = Depends(get_image_validator),
    metadata_service: ImageMetadata = Depends(get_metadata_service),
    storage_service: ImageStorage = Depends(get_storage_service),
    operation_service: ImageOperation = Depends(get_operation_service),
    query_service: ImageQuery = Depends(get_query_service),
    folders: Dict[str, str] = Depends(get_folders)
) -> FileController:
    """
    Dependency for creating a FileController with all its dependencies injected.
    This is the main entry point for FastAPI routes to get a controller.
    """
    return FileController(
        directory_manager=directory_manager,
        image_validator=image_validator,
        metadata_service=metadata_service,
        storage_service=storage_service,
        operation_service=operation_service,
        query_service=query_service,
        folders=folders
    )

def get_image_processing(
    image_query: ImageQuery = Depends(get_query_service)
) -> ImageProcessing:
    return ImageProcessing(image_query)