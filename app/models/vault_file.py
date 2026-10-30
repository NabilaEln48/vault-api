from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VaultFile(Base):
    __tablename__ = "vault_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    stored_name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    folder_id: Mapped[int | None] = mapped_column(
        ForeignKey("folders.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="files")
    folder: Mapped["Folder | None"] = relationship(back_populates="files")
    share_links: Mapped[list["ShareLink"]] = relationship(
        back_populates="file", cascade="all, delete-orphan"
    )
