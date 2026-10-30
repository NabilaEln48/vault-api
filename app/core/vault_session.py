from datetime import datetime, timedelta, timezone

from app.config import settings

_sessions: dict[int, tuple[bytes, datetime]] = {}


def _expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(
        minutes=settings.VAULT_SESSION_TTL_MINUTES
    )


def unlock(user_id: int, vault_key: bytes) -> None:
    _sessions[user_id] = (vault_key, _expiry())


def lock(user_id: int) -> None:
    _sessions.pop(user_id, None)


def get_key(user_id: int) -> bytes | None:
    entry = _sessions.get(user_id)
    if entry is None:
        return None
    vault_key, expires_at = entry
    if datetime.now(timezone.utc) >= expires_at:
        _sessions.pop(user_id, None)
        return None
    return vault_key


def is_unlocked(user_id: int) -> bool:
    return get_key(user_id) is not None
