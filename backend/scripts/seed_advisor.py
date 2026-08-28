"""Create / reset MusperSolutions' advisor account.

Idempotent: re-running it forces the account back to the documented state,
INCLUDING the password. That makes this script a reliable "reset advisor login"
button during development.

Usage:
    cd backend
    uv run python -m scripts.seed_advisor

    # Or with a custom password:
    ADVISOR_SEED_PASSWORD='YourPick1!' uv run python -m scripts.seed_advisor
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from anywhere, make sure the backend dir is on sys.path.
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
ADVISOR_FULL_NAME = os.environ.get("ADVISOR_SEED_NAME", "Penny")


def main() -> int:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == ADVISOR_EMAIL))
        if existing is not None:
            existing.role = UserRole.advisor
            existing.full_name = ADVISOR_FULL_NAME
            existing.is_verified = True
            existing.hashed_password = hash_password(ADVISOR_PASSWORD)
            # Wipe any half-finished reset / verification state.
            existing.reset_token_hash = None
            existing.reset_token_expires_at = None
            existing.verification_token_hash = None
            existing.verification_token_expires_at = None
            # Revoke every active refresh token, a password change should sign other sessions out.
            for rt in existing.refresh_tokens:
                if rt.revoked_at is None:
                    from datetime import datetime, timezone
                    rt.revoked_at = datetime.now(timezone.utc)
            db.add(existing)
            db.commit()
            print(f"✓ Advisor account reset to known state: {existing.email}")
            print(f"  Password: {ADVISOR_PASSWORD}")
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
        print(f"  Password: {ADVISOR_PASSWORD}")
        print("  ⚠  Change this on first login.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
