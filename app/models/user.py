from datetime import datetime

from sqlalchemy import DateTime, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    password_salt: Mapped[bytes] = mapped_column(LargeBinary(16))
    wrapped_vault_key: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    folders: Mapped[list["Folder"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    files: Mapped[list["VaultFile"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    share_links: Mapped[list["ShareLink"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )
