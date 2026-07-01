"""diagnostic_state JSONB column on diagnostic_sessions

Revision ID: 0005_diagnostic_state
Revises: 0004_dashboards
Create Date: 2026-06-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_diagnostic_state"
down_revision: Union[str, Sequence[str], None] = "0004_dashboards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "diagnostic_sessions",
        sa.Column("diagnostic_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("diagnostic_sessions", "diagnostic_state")
