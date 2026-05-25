"""Cookie helpers for the refresh token and the CSRF double-submit cookie."""
from datetime import datetime, timezone

from fastapi import Response

from app.core.config import settings

REFRESH_COOKIE = "musper_refresh"
CSRF_COOKIE = "musper_csrf"
CSRF_HEADER = "X-CSRF-Token"


def _max_age_seconds(expires_at: datetime) -> int:
    return max(0, int((expires_at - datetime.now(timezone.utc)).total_seconds()))


def set_auth_cookies(
    response: Response,
    *,
    refresh_token: str,
    csrf_token: str,
    expires_at: datetime,
) -> None:
    max_age = _max_age_seconds(expires_at)
    # The HTTP-only refresh cookie — never readable from JS.
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain or None,
    )
    # The CSRF cookie — readable from JS so the frontend can echo it back as a header.
    response.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        domain=settings.cookie_domain or None,
    )


def clear_auth_cookies(response: Response) -> None:
    for key in (REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(
            key=key,
            path="/",
            domain=settings.cookie_domain or None,
            secure=settings.cookie_secure,
            httponly=key == REFRESH_COOKIE,
            samesite="lax",
        )
