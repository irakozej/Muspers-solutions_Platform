import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

ALGO = "HS256"


# ───────────────────── passwords ─────────────────────

def hash_password(password: str) -> str:
    # bcrypt accepts at most 72 bytes — silently truncating is industry standard here.
    pw_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    pw_bytes = password.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
    except ValueError:
        return False


# ───────────────────── JWT access tokens ─────────────────────

def create_access_token(*, user_id: uuid.UUID, role: str) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.jwt_access_ttl_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGO)
    return token, expires_at


def decode_access_token(token: str) -> dict[str, Any]:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGO])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return payload


# ───────────────────── opaque refresh / reset / verify tokens ─────────────────────

def generate_opaque_token(nbytes: int = 48) -> str:
    """Return a URL-safe random token (the value sent to the client)."""
    return secrets.token_urlsafe(nbytes)


def hash_opaque_token(token: str) -> str:
    """Stable sha256 hex of an opaque token — what we store in the DB."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_eq(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def refresh_token_expiry(remember: bool) -> datetime:
    now = datetime.now(timezone.utc)
    days = settings.jwt_refresh_remember_ttl_days if remember else settings.jwt_refresh_ttl_days
    return now + timedelta(days=days)


def reset_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.reset_token_ttl_minutes)


def verify_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=settings.verify_token_ttl_hours)
