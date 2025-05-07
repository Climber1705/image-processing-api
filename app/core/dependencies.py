from pathlib import Path
from typing import Dict
from fastapi import Depends

from app.core.settings import settings
from app.services.file_management.directory_handler import DirectoryHandler
from app.services.file_management.image_verfication import ImageVerfication
from app.services.file_management.file_search import FileSearch
from app.services.file_management.file_utils import FileUtils
from app.services.file_management.storage_manager import StorageManager
from app.services.file_management.file_manager import FileManager

from app.services.data_processing.metadata_processor import MetadataProcessor
from app.services.data_processing.processing_manager import ProcessingManager

def get_directories() -> Dict[str, Path]:
    folders = {
        "uploads": settings.UPLOAD_FOLDER,
        "processed": settings.PROCESSED_FOLDER,
        "analzyed": settings.ANALYZED_FOLDER,
    }
    return folders

def get_directory_handler(
        directories: Dict[str, Path] = Depends(get_directories)
) -> DirectoryHandler:
    return DirectoryHandler(directories)

def get_image_verifcation() -> ImageVerfication:
    return ImageVerfication()

def get_metadata_processor() -> MetadataProcessor:
    return MetadataProcessor()

def get_file_search(
    directory_handler: DirectoryHandler = Depends(get_directory_handler),
    metadata_processor: MetadataProcessor = Depends(get_metadata_processor)
) -> FileSearch:
    return FileSearch(directory_handler, metadata_processor)

def get_file_utils(
    directory_handler: DirectoryHandler = Depends(get_directory_handler),
    metadata_processor: MetadataProcessor = Depends(get_metadata_processor)    
) -> FileUtils:
    return FileUtils(directory_handler, metadata_processor)

def get_storage_manager(
    directory_handler: DirectoryHandler = Depends(get_directory_handler),
    image_verification: ImageVerfication = Depends(get_image_verifcation)  
) -> StorageManager:
    return StorageManager(directory_handler, image_verification)

def get_file_manager(
    directory_handler: DirectoryHandler = Depends(get_directory_handler),
    image_verification: ImageVerfication = Depends(get_image_verifcation),
    metadata_processor: MetadataProcessor = Depends(get_metadata_processor),
    storage_manager: StorageManager = Depends(get_storage_manager),
    file_utils: FileUtils = Depends(get_file_utils),
    file_search: FileSearch = Depends(get_file_search),
    folder: Dict[str, Path] = Depends(get_directories)

) -> FileManager:
    return FileManager(directory_handler, image_verification, metadata_processor, storage_manager, file_utils, file_search, folder)

def get_processing_manager() -> ProcessingManager:
    return ProcessingManager()