"""Create missing Client profile rows for client-role users.

Registration now creates the profile at signup; this repairs accounts created
before that fix. Idempotent: users who already have a profile are untouched,
so it is safe to run repeatedly.

Run from backend/ against the local database:

    uv run python scripts/repair_missing_client_profiles.py

Against another database (e.g. Render production), point DATABASE_URL at it:

    DATABASE_URL='<external-database-url>' uv run python scripts/repair_missing_client_profiles.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models.client import Client  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        orphans = db.scalars(
            select(User).where(
                User.role == UserRole.client,
                ~User.client_profile.has(),
            )
        ).all()
        if not orphans:
            print("All client-role users already have a profile. Nothing to do.")
            return
        for user in orphans:
            db.add(Client(user_id=user.id))
            print(f"  + created profile for {user.email}")
        db.commit()
        print(f"Done. Created {len(orphans)} profile(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
