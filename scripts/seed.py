import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.core.crypto import (
    encrypt_bytes,
    generate_salt,
    generate_vault_key,
    sha256_hex,
    wrap_file_key,
    wrap_vault_key,
)
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.folder import Folder
from app.models.user import User
from app.models.vault_file import VaultFile

import uuid

Base.metadata.create_all(bind=engine)

db = SessionLocal()
email = "demo@vault.dev"
password = "demo1234"

user = db.query(User).filter(User.email == email).first()
if user is None:
    salt = generate_salt()
    vault_key = generate_vault_key()
    user = User(
        email=email,
        hashed_password=hash_password(password),
        password_salt=salt,
        wrapped_vault_key=wrap_vault_key(vault_key, password, salt),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

from app.core.crypto import unwrap_vault_key

vault_key = unwrap_vault_key(user.wrapped_vault_key, password, user.password_salt)

documents = db.query(Folder).filter(
    Folder.owner_id == user.id, Folder.name == "Documents"
).first()
if documents is None:
    documents = Folder(name="Documents", owner_id=user.id)
    db.add(documents)
    db.commit()
    db.refresh(documents)

photos = db.query(Folder).filter(
    Folder.owner_id == user.id, Folder.name == "Photos"
).first()
if photos is None:
    photos = Folder(name="Photos", owner_id=user.id)
    db.add(photos)
    db.commit()
    db.refresh(photos)

samples = [
    ("welcome.txt", b"Welcome to your vault. This file is encrypted at rest.", documents.id),
    ("notes.txt", b"Vault rule one: never store a password in plain text.", documents.id),
]
for original_name, content, folder_id in samples:
    existing = (
        db.query(VaultFile)
        .filter(VaultFile.owner_id == user.id, VaultFile.original_name == original_name)
        .first()
    )
    if existing is not None:
        continue
    file_key = generate_vault_key()
    stored_name = uuid.uuid4().hex + ".enc"
    directory = Path(settings.VAULT_DIR) / str(user.id)
    directory.mkdir(parents=True, exist_ok=True)
    directory.joinpath(stored_name).write_bytes(encrypt_bytes(file_key, content))
    row = VaultFile(
        stored_name=stored_name,
        original_name=original_name,
        content_type="text/plain",
        size_bytes=len(content),
        sha256=sha256_hex(content),
        wrapped_key=wrap_file_key(file_key, vault_key),
        owner_id=user.id,
        folder_id=folder_id,
    )
    db.add(row)
    db.commit()

print(f"Seeded demo user {email} with password {password}")
db.close()
