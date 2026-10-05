"""DATABASE_URL normalisation for managed Postgres hosts (Neon in production)."""
from alembic.config import Config
from sqlalchemy.engine import make_url

from app.core.config import Settings

NEON = "postgresql://user:pass@ep-cool-name-123456.eu-central-1.aws.neon.tech/dbname?sslmode=require"


def test_neon_url_uses_psycopg_and_keeps_sslmode():
    url = Settings(database_url=NEON).database_url
    assert url == NEON.replace("postgresql://", "postgresql+psycopg://", 1)
    parsed = make_url(url)
    assert parsed.drivername == "postgresql+psycopg"
    assert parsed.query["sslmode"] == "require"
    assert (parsed.host, parsed.database, parsed.username) == (
        "ep-cool-name-123456.eu-central-1.aws.neon.tech", "dbname", "user")


def test_postgres_scheme_and_explicit_driver():
    assert Settings(database_url="postgres://u:p@h/d?sslmode=require").database_url == \
        "postgresql+psycopg://u:p@h/d?sslmode=require"
    explicit = "postgresql+psycopg://u:p@h/d"
    assert Settings(database_url=explicit).database_url == explicit


def test_alembic_accepts_url_encoded_password():
    # Mirrors alembic/env.py: % must be escaped for ConfigParser.
    url = Settings(database_url="postgresql://u:p%40ss@h/d?sslmode=require").database_url
    cfg = Config()
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    assert cfg.get_main_option("sqlalchemy.url") == url
    assert make_url(url).password == "p@ss"
