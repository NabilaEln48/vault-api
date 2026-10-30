from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import vault_session
from app.core.crypto import (
    generate_salt,
    generate_vault_key,
    unwrap_vault_key,
    wrap_vault_key,
)
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.user import PasswordChange, Token, UnlockRequest, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    salt = generate_salt()
    vault_key = generate_vault_key()
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        password_salt=salt,
        wrapped_vault_key=wrap_vault_key(vault_key, payload.password, salt),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form.username).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password", response_model=UserOut)
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    vault_key = unwrap_vault_key(
        user.wrapped_vault_key, payload.current_password, user.password_salt
    )
    new_salt = generate_salt()
    user.hashed_password = hash_password(payload.new_password)
    user.password_salt = new_salt
    user.wrapped_vault_key = wrap_vault_key(vault_key, payload.new_password, new_salt)
    vault_session.lock(user.id)
    db.commit()
    db.refresh(user)
    return user
