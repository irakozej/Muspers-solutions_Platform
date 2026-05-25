"""Test fixtures — uses a dedicated `musper_test` Postgres database.

The dev database is left untouched. We drop+recreate the public schema once per
test session, then truncate auth tables between tests.
"""
from __future__ import annotations

import os

import psycopg

TEST_DB_NAME = "musper_test"
TEST_DB_URL = f"postgresql+psycopg://musper:musper@localhost:5434/{TEST_DB_NAME}"

# Must run BEFORE the app is imported so settings pick up the test DB URL.
os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ["APP_ENV"] = "development"  # auto-verifies signups
os.environ["JWT_SECRET"] = "tests-do-not-use-this-secret-anywhere-else-please"
os.environ["COOKIE_SECURE"] = "false"
os.environ["FRONTEND_URL"] = "http://localhost:5173"


def _ensure_test_db_exists() -> None:
    admin_url = "postgresql://musper:musper@localhost:5434/postgres"
    with psycopg.connect(admin_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB_NAME,))
            if cur.fetchone() is None:
                cur.execute(f"CREATE DATABASE {TEST_DB_NAME}")


_ensure_test_db_exists()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# Reset the cached settings so the env override above sticks.
from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app import models  # noqa: F401, E402  (register all models on the metadata)
from app.core.limiter import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402

TRUNCATE_TABLES = ("refresh_tokens", "users", "contact_submissions")


@pytest.fixture(scope="session", autouse=True)
def _setup_schema():
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE")
        conn.exec_driver_sql("CREATE SCHEMA public")
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _between_tests():
    # Rate limiting off by default for tests; tests that want it can flip it.
    limiter.enabled = False
    yield
    with engine.begin() as conn:
        conn.exec_driver_sql(
            f"TRUNCATE {', '.join(TRUNCATE_TABLES)} RESTART IDENTITY CASCADE"
        )


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def csrf_headers(client: TestClient) -> dict[str, str]:
    csrf = client.cookies.get("musper_csrf")
    return {"X-CSRF-Token": csrf} if csrf else {}
