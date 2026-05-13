from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from cloud_backend.db.base import Base


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_id: Mapped[int] = mapped_column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    upload_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    total_parts: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
