import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ImageRecord(Base):
    __tablename__ = "images"
    __table_args__ = (
        UniqueConstraint("filename", "folder", name="uq_images_filename_folder"),
        UniqueConstraint("content_hash", "folder", name="uq_images_content_hash_folder"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255), index=True)
    folder: Mapped[str] = mapped_column(String(50), index=True)
    path: Mapped[str] = mapped_column(String(512))
    format: Mapped[str] = mapped_column(String(20))
    mode: Mapped[str] = mapped_column(String(20))
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
