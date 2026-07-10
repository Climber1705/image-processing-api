import uuid
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.media.domain.dtos import ImageDTO
from app.media.domain.errors import ImageCreationError
from app.media.utils.mappers import record_to_dto
from app.media.utils.metadata import get_image_metadata
from app.models.image import ImageRecord


class ImageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        image_id: str,
        path: str | Path,
        folder: str,
        display_filename: str,
        content_hash: str,
    ) -> ImageDTO:
        path = Path(path)
        metadata = get_image_metadata(path)
        record = ImageRecord(
            id=image_id,
            filename=display_filename,
            folder=folder,
            path=str(path),
            format=metadata.format,
            mode=metadata.mode,
            width=metadata.width,
            height=metadata.height,
            size_bytes=metadata.size_bytes,
            content_hash=content_hash,
        )
        try:
            self.session.add(record)
            self.session.commit()
            self.session.refresh(record)
            return record_to_dto(record)
        except IntegrityError as exc:
            self.session.rollback()
            raise ImageCreationError("Failed to create image record") from exc

    def upsert(
        self,
        path: str | Path,
        folder: str,
        display_filename: str,
        image_id: str,
        content_hash: str | None = None,
    ) -> ImageDTO:
        path = Path(path)
        metadata = get_image_metadata(path)

        existing_record = self.get_by_filename(display_filename, folder)
        if existing_record is not None:
            existing_record.path = str(path)
            existing_record.format = metadata.format
            existing_record.mode = metadata.mode
            existing_record.width = metadata.width
            existing_record.height = metadata.height
            existing_record.size_bytes = metadata.size_bytes
            if content_hash is not None:
                existing_record.content_hash = content_hash
            self.session.commit()
            self.session.refresh(existing_record)
            return record_to_dto(existing_record)

        record = ImageRecord(
            id=image_id,
            filename=display_filename,
            folder=folder,
            path=str(path),
            format=metadata.format,
            mode=metadata.mode,
            width=metadata.width,
            height=metadata.height,
            size_bytes=metadata.size_bytes,
            content_hash=content_hash,
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record_to_dto(record)

    def get_by_filename(self, filename: str, folder: str) -> ImageRecord | None:
        return self.session.scalar(
            select(ImageRecord).where(
                ImageRecord.filename == filename,
                ImageRecord.folder == folder,
            )
        )

    def get_or_create_image_id(self, display_filename: str, folder: str) -> str:
        record = self.get_by_filename(display_filename, folder)
        if record is not None:
            return record.id
        return str(uuid.uuid4())

    def get_by_content_hash(self, content_hash: str, folder: str) -> ImageRecord | None:
        return self.session.scalar(
            select(ImageRecord).where(
                ImageRecord.content_hash == content_hash,
                ImageRecord.folder == folder,
            )
        )

    def get_by_folder(
        self,
        folders: list[str],
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageRecord]:
        statement = (
            select(ImageRecord)
            .where(ImageRecord.folder.in_(folders))
            .order_by(ImageRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def get_all_by_folders(self, folders: list[str]) -> list[ImageRecord]:
        statement = (
            select(ImageRecord)
            .where(ImageRecord.folder.in_(folders))
            .order_by(ImageRecord.created_at.desc())
        )
        return list(self.session.scalars(statement).all())

    def delete_by_filename(self, filename: str, folder: str) -> bool:
        record = self.get_by_filename(filename, folder)
        if record is None:
            return False

        self.session.delete(record)
        self.session.commit()
        return True

    def delete_by_folders(self, folders: list[str]) -> int:
        result = self.session.execute(delete(ImageRecord).where(ImageRecord.folder.in_(folders)))
        self.session.commit()
        return result.rowcount or 0

    def update(
        self,
        filename: str,
        source_folder: str,
        target_folder: str,
        new_path: str,
    ) -> ImageDTO | None:
        record = self.get_by_filename(filename, source_folder)
        if record is None:
            return None

        record.folder = target_folder
        record.path = new_path
        self.session.commit()
        self.session.refresh(record)
        return record_to_dto(record)
