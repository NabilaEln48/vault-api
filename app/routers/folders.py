from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.folder import Folder
from app.models.user import User
from app.models.vault_file import VaultFile
from app.schemas.folder import FolderCreate, FolderOut, FolderUpdate

router = APIRouter(prefix="/folders", tags=["folders"])


def _get_folder(db: Session, folder_id: int, user: User) -> Folder:
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


def _descendant_ids(db: Session, folder: Folder) -> list[int]:
    ids = [folder.id]
    queue = [folder.id]
    while queue:
        current = queue.pop()
        children = db.query(Folder).filter(Folder.parent_id == current).all()
        for child in children:
            ids.append(child.id)
            queue.append(child.id)
    return ids


@router.post("", response_model=FolderOut, status_code=status.HTTP_201_CREATED)
def create_folder(
    payload: FolderCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.parent_id is not None:
        _get_folder(db, payload.parent_id, user)
    folder = Folder(
        name=payload.name, owner_id=user.id, parent_id=payload.parent_id
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


@router.get("", response_model=list[FolderOut])
def list_folders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Folder)
        .filter(Folder.owner_id == user.id)
        .order_by(Folder.name)
        .all()
    )


@router.get("/{folder_id}", response_model=FolderOut)
def get_folder(
    folder_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_folder(db, folder_id, user)


@router.patch("/{folder_id}", response_model=FolderOut)
def update_folder(
    folder_id: int,
    payload: FolderUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    folder = _get_folder(db, folder_id, user)
    if payload.name is not None:
        folder.name = payload.name
    if payload.parent_id is not None:
        if payload.parent_id == folder.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A folder cannot be its own parent",
            )
        _get_folder(db, payload.parent_id, user)
        folder.parent_id = payload.parent_id
    db.commit()
    db.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    folder = _get_folder(db, folder_id, user)
    tree_ids = _descendant_ids(db, folder)
    db.query(VaultFile).filter(VaultFile.folder_id.in_(tree_ids)).update(
        {"folder_id": None}, synchronize_session=False
    )
    db.delete(folder)
    db.commit()
    return None
