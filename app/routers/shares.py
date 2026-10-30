import secrets
from datetime import datetime, timedelta, timezone

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.crypto import derive_share_key, unwrap_file_key, decrypt_bytes
from app.core.deps import get_current_user, require_unlocked_vault
from app.database import get_db
from app.models.share_link import ShareLink
from app.models.user import User
from app.models.vault_file import VaultFile
from app.routers.files import _get_file, _user_dir
from app.schemas.share_link import ShareCreate, ShareLinkOut

router = APIRouter(tags=["shares"])


def _aware(moment: datetime | None) -> datetime | None:
    if moment is None:
        return None
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment


@router.post(
    "/files/{file_id}/shares",
    response_model=ShareLinkOut,
    status_code=status.HTTP_201_CREATED,
)
def create_share(
    file_id: int,
    payload: ShareCreate,
    vault_key: bytes = Depends(require_unlocked_vault),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _get_file(db, file_id, user)
    file_key = unwrap_file_key(row.wrapped_key, vault_key)
    token = secrets.token_urlsafe(32)
    wrapped_file_key = Fernet(derive_share_key(token)).encrypt(file_key)
    expires_at = None
    if payload.expires_in_minutes is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=payload.expires_in_minutes
        )
    link = ShareLink(
        token=token,
        file_id=row.id,
        created_by=user.id,
        wrapped_file_key=wrapped_file_key,
        expires_at=expires_at,
        max_downloads=payload.max_downloads,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    out = ShareLinkOut.model_validate(link)
    out.url = f"/shares/{token}"
    return out


@router.get("/shares", response_model=list[ShareLinkOut])
def list_shares(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    links = (
        db.query(ShareLink)
        .filter(ShareLink.created_by == user.id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )
    result = []
    for link in links:
        out = ShareLinkOut.model_validate(link)
        out.url = f"/shares/{link.token}"
        result.append(out)
    return result


@router.delete("/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_share(
    share_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    link = (
        db.query(ShareLink)
        .filter(ShareLink.id == share_id, ShareLink.created_by == user.id)
        .first()
    )
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found"
        )
    db.delete(link)
    db.commit()
    return None


@router.get("/shares/{token}")
def download_shared_file(token: str, db: Session = Depends(get_db)):
    link = db.query(ShareLink).filter(ShareLink.token == token).first()
    if link is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Share link not found"
        )
    now = datetime.now(timezone.utc)
    if _aware(link.expires_at) is not None and _aware(link.expires_at) < now:
        raise HTTPException(
            status_code=status.HTTP_410_GONE, detail="Share link has expired"
        )
    if link.max_downloads is not None and link.download_count >= link.max_downloads:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link download limit reached",
        )
    row = db.get(VaultFile, link.file_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    path = _user_dir(row.owner_id) / row.stored_name
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stored file is missing"
        )
    file_key = Fernet(derive_share_key(token)).decrypt(link.wrapped_file_key)
    plaintext = decrypt_bytes(file_key, path.read_bytes())
    link.download_count += 1
    db.commit()
    return Response(
        content=plaintext,
        media_type=row.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{row.original_name}"'
        },
    )
