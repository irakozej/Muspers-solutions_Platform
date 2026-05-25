"""Create or update Penny's advisor account. Idempotent — safe to re-run.

Usage:
    cd backend
    uv run python -m scripts.seed_advisor
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from anywhere — make sure the project root is on sys.path.
HERE = Path(__file__).resolve()
BACKEND_DIR = HERE.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402

ADVISOR_EMAIL = "penny@muspersolutions.com"
ADVISOR_PASSWORD = os.environ.get("ADVISOR_SEED_PASSWORD", "ChangeMe2026!")
ADVISOR_FULL_NAME = "Penny Burabyo Musoni"


def main() -> int:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == ADVISOR_EMAIL))
        if existing is not None:
            existing.role = UserRole.advisor
            existing.full_name = ADVISOR_FULL_NAME
            existing.is_verified = True
            db.add(existing)
            db.commit()
            print(f"✓ Advisor already present — refreshed profile: {existing.email}")
            return 0

        advisor = User(
            email=ADVISOR_EMAIL,
            hashed_password=hash_password(ADVISOR_PASSWORD),
            role=UserRole.advisor,
            full_name=ADVISOR_FULL_NAME,
            is_verified=True,
        )
        db.add(advisor)
        db.commit()
        print(f"✓ Created advisor account: {ADVISOR_EMAIL}")
        print(f"  Initial password: {ADVISOR_PASSWORD}")
        print("  ⚠  Change this on first login.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
