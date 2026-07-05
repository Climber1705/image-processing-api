import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models.image import ImageRecord
from app.media.metadata_handler import ImageMetadataExtractor


class ImageRepository:
    def __init__(self, session: Session, metadata_extractor: ImageMetadataExtractor):
        self.session = session
        self.metadata_extractor = metadata_extractor

    def create_from_path(self, path: str | Path, folder: str) -> ImageRecord:
        path = Path(path)
        metadata = self.metadata_extractor.get_metadata(path)

        existing = self.get_by_filename(path.name, folder)
        if existing is not None:
            existing.path = str(path)
            existing.format = metadata["format"]
            existing.mode = metadata["mode"]
            existing.width = metadata["width"]
            existing.height = metadata["height"]
            existing.size_bytes = metadata["size_bytes"]
            self.session.commit()
            self.session.refresh(existing)
            return existing

        record = ImageRecord(
            id=str(uuid.uuid4()),
            filename=path.name,
            folder=folder,
            path=str(path),
            format=metadata["format"],
            mode=metadata["mode"],
            width=metadata["width"],
            height=metadata["height"],
            size_bytes=metadata["size_bytes"],
        )
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def get_by_id(self, image_id: str) -> ImageRecord | None:
        return self.session.get(ImageRecord, image_id)

    def get_by_filename(self, filename: str, folder: str) -> ImageRecord | None:
        return self.session.scalar(
            select(ImageRecord).where(
                ImageRecord.filename == filename,
                ImageRecord.folder == folder,
            )
        )

    def get_by_filename_any_folder(self, filename: str) -> ImageRecord | None:
        return self.session.scalar(
            select(ImageRecord)
            .where(ImageRecord.filename == filename)
            .order_by(ImageRecord.created_at.desc())
        )

    def list_by_folder(
        self,
        folders: list[str],
        limit: int = 100,
        offset: int = 0,
    ) -> list[ImageRecord]:
        stmt = (
            select(ImageRecord)
            .where(ImageRecord.folder.in_(folders))
            .order_by(ImageRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).all())

    def list_all_by_folders(self, folders: list[str]) -> list[ImageRecord]:
        stmt = (
            select(ImageRecord)
            .where(ImageRecord.folder.in_(folders))
            .order_by(ImageRecord.created_at.desc())
        )
        return list(self.session.scalars(stmt).all())

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

    def update_location(
        self,
        filename: str,
        source_folder: str,
        target_folder: str,
        new_path: str,
    ) -> ImageRecord | None:
        record = self.get_by_filename(filename, source_folder)
        if record is None:
            return None

        record.folder = target_folder
        record.path = new_path
        record.filename = Path(new_path).name
        self.session.commit()
        self.session.refresh(record)
        return record

    @staticmethod
    def to_metadata(record: ImageRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "filename": record.filename,
            "format": record.format,
            "mode": record.mode,
            "width": record.width,
            "height": record.height,
            "size_bytes": record.size_bytes,
            "path": record.path,
            "url": None,
            "folder": record.folder,
        }
