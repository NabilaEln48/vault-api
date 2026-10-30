from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ShareCreate(BaseModel):
    expires_in_minutes: int | None = None
    max_downloads: int | None = None


class ShareLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    file_id: int
    expires_at: datetime | None
    max_downloads: int | None
    download_count: int
    created_at: datetime
    url: str = ""
