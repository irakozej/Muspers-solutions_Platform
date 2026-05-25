"""All authentication business logic — kept thin and explicit.

Dev-mode behaviour:
  - Signups are auto-verified (is_verified=True) but still receive a verification
    token in case the frontend wants to round-trip it.
  - Reset / verification tokens are logged to stdout so manual testing can
    follow the link without a real SMTP server.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    generate_opaque_token,
    hash_opaque_token,
    hash_password,
    refresh_token_expiry,
    reset_token_expiry,
    verify_password,
    verify_token_expiry,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole

log = logging.getLogger("musper.auth")


# ───────────────────── helpers ─────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _email_taken_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")


def _invalid_credentials() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")


def _log_dev_link(*, purpose: str, email: str, token: str, path: str) -> str:
    link = f"{settings.frontend_url.rstrip('/')}{path}?token={token}"
    log.warning("\n  ✉  [DEV] %s for %s\n     %s\n", purpose, email, link)
    return link


# ───────────────────── core flows ─────────────────────

def register_client(db: Session, *, email: str, password: str, full_name: str) -> tuple[User, str]:
    """Create a new client account. Returns (user, verification_token)."""
    email = email.lower().strip()

    verify_token = generate_opaque_token()
    verify_hash = hash_opaque_token(verify_token)

    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.client,
        full_name=full_name.strip(),
        is_verified=settings.is_dev,  # auto-verify in dev
        verification_token_hash=verify_hash,
        verification_token_expires_at=verify_token_expiry(),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _email_taken_error()
    db.refresh(user)

    _log_dev_link(
        purpose="Email verification",
        email=user.email,
        token=verify_token,
        path="/verify-email",
    )
    return user, verify_token


def authenticate(db: Session, *, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or not verify_password(password, user.hashed_password):
        raise _invalid_credentials()
    return user


def issue_refresh_token(
    db: Session,
    *,
    user: User,
    remember: bool,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[str, datetime]:
    token = generate_opaque_token()
    expires_at = refresh_token_expiry(remember=remember)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_opaque_token(token),
            expires_at=expires_at,
            user_agent=(user_agent or "")[:500] or None,
            ip_address=(ip_address or "")[:64] or None,
        )
    )
    db.commit()
    return token, expires_at


def rotate_refresh_token(
    db: Session,
    *,
    raw_token: str,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[User, str, datetime]:
    """Validate the presented refresh token, revoke it, issue a fresh one."""
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw_token))
    )
    if record is None or record.revoked_at is not None or record.expires_at < _now():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
        )

    user = db.get(User, record.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: revoke the presented one, issue a new one with the same TTL window
    # (preserves the "remember me" behaviour across refreshes).
    remember_window = (record.expires_at - record.issued_at).days > settings.jwt_refresh_ttl_days
    record.revoked_at = _now()
    record.last_used_at = _now()
    db.add(record)

    new_token, new_exp = issue_refresh_token(
        db, user=user, remember=remember_window, user_agent=user_agent, ip_address=ip_address
    )
    return user, new_token, new_exp


def revoke_refresh_token(db: Session, *, raw_token: str) -> None:
    record = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_opaque_token(raw_token))
    )
    if record and record.revoked_at is None:
        record.revoked_at = _now()
        db.add(record)
        db.commit()


# ───────────────────── password reset & verification ─────────────────────

def issue_password_reset(db: Session, *, email: str) -> None:
    """Always returns silently — never reveal whether an email exists."""
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None:
        return

    raw = generate_opaque_token()
    user.reset_token_hash = hash_opaque_token(raw)
    user.reset_token_expires_at = reset_token_expiry()
    db.add(user)
    db.commit()
    _log_dev_link(
        purpose="Password reset", email=user.email, token=raw, path="/reset-password"
    )


def consume_password_reset(db: Session, *, token: str, new_password: str) -> User:
    token_hash = hash_opaque_token(token)
    user = db.scalar(select(User).where(User.reset_token_hash == token_hash))
    if (
        user is None
        or user.reset_token_expires_at is None
        or user.reset_token_expires_at < _now()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or expired",
        )
    user.hashed_password = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    # Invalidate every active session — password change is a security event.
    for rt in user.refresh_tokens:
        if rt.revoked_at is None:
            rt.revoked_at = _now()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def consume_verification(db: Session, *, token: str) -> User:
    token_hash = hash_opaque_token(token)
    user = db.scalar(select(User).where(User.verification_token_hash == token_hash))
    if (
        user is None
        or user.verification_token_expires_at is None
        or user.verification_token_expires_at < _now()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is invalid or expired",
        )
    user.is_verified = True
    user.verification_token_hash = None
    user.verification_token_expires_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ───────────────────── profile ─────────────────────

def update_profile(
    db: Session, *, user: User, full_name: str | None, email: str | None
) -> User:
    changed = False
    if full_name is not None and full_name.strip() != (user.full_name or ""):
        user.full_name = full_name.strip()
        changed = True
    if email is not None:
        new_email = email.lower().strip()
        if new_email != user.email:
            existing = db.scalar(select(User).where(User.email == new_email))
            if existing is not None and existing.id != user.id:
                raise _email_taken_error()
            user.email = new_email
            user.is_verified = settings.is_dev  # require re-verification in real envs
            changed = True
    if changed:
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def change_password(
    db: Session, *, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    user.hashed_password = hash_password(new_password)
    # Same as reset — revoke all other sessions.
    for rt in user.refresh_tokens:
        if rt.revoked_at is None:
            rt.revoked_at = _now()
    db.add(user)
    db.commit()
