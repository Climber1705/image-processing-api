from fastapi import Depends
from sqlalchemy.orm import Session


from app.db.session import get_db
from app.media.repository import ImageRepository

def get_image_repository(session: Session = Depends(get_db)) -> ImageRepository:
    return ImageRepository(session=session)
