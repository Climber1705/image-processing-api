from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.repository import ImageRepository
from app.db.session import get_db
from app.media.metadata_handler import ImageMetadataExtractor


def get_image_metadata_extractor() -> ImageMetadataExtractor:
    return ImageMetadataExtractor()


def get_image_repository(
    session: Session = Depends(get_db),
    metadata_extractor: ImageMetadataExtractor = Depends(get_image_metadata_extractor),
) -> ImageRepository:
    return ImageRepository(session=session, metadata_extractor=metadata_extractor)
