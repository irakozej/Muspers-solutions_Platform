from sqlalchemy import select

from app.core.security import (
    generate_opaque_token,
    hash_opaque_token,
    reset_token_expiry,
)
from app.models.user import User

from .conftest import csrf_headers

EMAIL = "alice@example.com"
PASSWORD = "Super-Secret-1!"
NAME = "Alice Mukamana"


def _register(client, email=EMAIL, password=PASSWORD, name=NAME):
    return client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )


def _login(client, email=EMAIL, password=PASSWORD, remember=False):
    return client.post(
        "/api/auth/login",
        json={"email": email, "password": password, "remember": remember},
    )


def test_register_creates_client_user(client):
    r = _register(client)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == EMAIL
    assert body["user"]["role"] == "client"
    assert body["user"]["full_name"] == NAME
    assert body["access_token"]
    assert client.cookies.get("musper_refresh")
    assert client.cookies.get("musper_csrf")


def test_register_rejects_duplicate_email(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 409


def test_login_with_valid_credentials_sets_cookies(client):
    _register(client)
    client.cookies.clear()
    r = _login(client)
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]
    assert client.cookies.get("musper_refresh")


def test_login_with_wrong_password_returns_401(client):
    _register(client)
    client.cookies.clear()
    r = _login(client, password="not-the-right-password")
    assert r.status_code == 401


def test_me_with_valid_token_returns_user(client):
    r = _register(client)
    token = r.json()["access_token"]
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["email"] == EMAIL


def test_me_without_token_returns_401(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_refresh_rotates_and_returns_new_access_token(client):
    _register(client)
    r = client.post("/api/auth/refresh", headers=csrf_headers(client))
    assert r.status_code == 200, r.text
    assert r.json()["access_token"]


def test_refresh_without_csrf_header_returns_403(client):
    _register(client)
    r = client.post("/api/auth/refresh")
    assert r.status_code == 403


def test_logout_revokes_refresh_token(client):
    _register(client)
    r = client.post("/api/auth/logout", headers=csrf_headers(client))
    assert r.status_code == 200
    # cookies should be cleared; refresh attempts fail
    r2 = client.post("/api/auth/refresh", headers=csrf_headers(client))
    assert r2.status_code in (401, 403)


def test_password_reset_end_to_end(client, db_session):
    _register(client)
    # Mint a reset token directly (mirrors what /forgot-password does, but lets
    # us grab the raw token for the test).
    user = db_session.scalar(select(User).where(User.email == EMAIL))
    raw = generate_opaque_token()
    user.reset_token_hash = hash_opaque_token(raw)
    user.reset_token_expires_at = reset_token_expiry()
    db_session.add(user)
    db_session.commit()

    r = client.post(
        "/api/auth/reset-password",
        json={"token": raw, "new_password": "Brand-New-2026!"},
    )
    assert r.status_code == 200, r.text

    client.cookies.clear()
    assert _login(client, password=PASSWORD).status_code == 401
    assert _login(client, password="Brand-New-2026!").status_code == 200


def test_profile_update_requires_csrf(client):
    r = _register(client)
    token = r.json()["access_token"]
    # No CSRF — should be rejected
    r2 = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Alice U."},
    )
    assert r2.status_code == 403


def test_profile_update_changes_full_name(client):
    r = _register(client)
    token = r.json()["access_token"]
    r2 = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}", **csrf_headers(client)},
        json={"full_name": "Alice U."},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["full_name"] == "Alice U."
