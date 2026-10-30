import hashlib
import secrets
from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


def derive_kek(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=settings.KDF_ITERATIONS,
    )
    return urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def generate_vault_key() -> bytes:
    return Fernet.generate_key()


def generate_salt() -> bytes:
    return secrets.token_bytes(16)


def wrap_vault_key(vault_key: bytes, password: str, salt: bytes) -> bytes:
    return Fernet(derive_kek(password, salt)).encrypt(vault_key)


def unwrap_vault_key(wrapped: bytes, password: str, salt: bytes) -> bytes:
    try:
        return Fernet(derive_kek(password, salt)).decrypt(wrapped)
    except InvalidToken:
        raise ValueError("wrong password") from None


def encrypt_bytes(vault_key: bytes, plaintext: bytes) -> bytes:
    return Fernet(vault_key).encrypt(plaintext)


def decrypt_bytes(vault_key: bytes, token: bytes) -> bytes:
    try:
        return Fernet(vault_key).decrypt(token)
    except InvalidToken:
        raise ValueError("cannot decrypt file") from None


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wrap_file_key(file_key: bytes, vault_key: bytes) -> bytes:
    return Fernet(vault_key).encrypt(file_key)


def unwrap_file_key(wrapped: bytes, vault_key: bytes) -> bytes:
    try:
        return Fernet(vault_key).decrypt(wrapped)
    except InvalidToken:
        raise ValueError("cannot unwrap file key") from None


def derive_share_key(token: str) -> bytes:
    return urlsafe_b64encode(hashlib.sha256(token.encode("utf-8")).digest())
