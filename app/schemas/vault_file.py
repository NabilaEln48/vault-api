from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VaultFileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_name: str
    content_type: str
    size_bytes: int
    sha256: str
    folder_id: int | None
    created_at: datetime


class VaultFileUpdate(BaseModel):
    original_name: str | None = None
    folder_id: int | None = None
