"""clients.business_name nullable, profiles are created empty at signup

Revision ID: 0006_client_name_nullable
Revises: 0005_diagnostic_state
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_client_name_nullable"
down_revision: Union[str, Sequence[str], None] = "0005_diagnostic_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "clients",
        "business_name",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    # Backfill a placeholder so the NOT NULL constraint can be restored.
    op.execute("UPDATE clients SET business_name = 'Unnamed business' WHERE business_name IS NULL")
    op.alter_column(
        "clients",
        "business_name",
        existing_type=sa.String(length=255),
        nullable=False,
    )
