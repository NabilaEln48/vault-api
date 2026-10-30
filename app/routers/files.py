import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.core.crypto import (
    decrypt_bytes,
    encrypt_bytes,
    generate_vault_key,
    sha256_hex,
    unwrap_file_key,
    wrap_file_key,
)
from app.core.deps import get_current_user, require_unlocked_vault
from app.database import get_db
from app.models.folder import Folder
from app.models.user import User
from app.models.vault_file import VaultFile
from app.schemas.vault_file import VaultFileOut, VaultFileUpdate

router = APIRouter(prefix="/files", tags=["files"])


def _user_dir(user_id: int) -> Path:
    path = Path(settings.VAULT_DIR) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _get_file(db: Session, file_id: int, user: User) -> VaultFile:
    row = (
        db.query(VaultFile)
        .filter(VaultFile.id == file_id, VaultFile.owner_id == user.id)
        .first()
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return row


def _get_owned_folder(db: Session, folder_id: int, user: User) -> Folder:
    folder = (
        db.query(Folder)
        .filter(Folder.id == folder_id, Folder.owner_id == user.id)
        .first()
    )
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Folder not found"
        )
    return folder


@router.post("", response_model=VaultFileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    folder_id: int | None = Form(None),
    vault_key: bytes = Depends(require_unlocked_vault),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if folder_id is not None:
        _get_owned_folder(db, folder_id, user)
    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds the maximum upload size",
        )
    file_key = generate_vault_key()
    stored_name = uuid.uuid4().hex + ".enc"
    _user_dir(user.id).joinpath(stored_name).write_bytes(
        encrypt_bytes(file_key, content)
    )
    row = VaultFile(
        stored_name=stored_name,
        original_name=file.filename or stored_name,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        sha256=sha256_hex(content),
        wrapped_key=wrap_file_key(file_key, vault_key),
        owner_id=user.id,
        folder_id=folder_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
