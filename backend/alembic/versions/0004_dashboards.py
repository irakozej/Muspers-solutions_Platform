"""dashboards: extend clients + add advisor_notes

Revision ID: 0004_dashboards
Revises: 0003_auth
Create Date: 2026-05-26 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_dashboards"
down_revision: Union[str, Sequence[str], None] = "0003_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend clients with business metadata
    business_size_enum = postgresql.ENUM(
        "micro", "small", "medium", "large", name="business_size"
    )
    business_size_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "clients",
        sa.Column("business_size", business_size_enum, nullable=True),
    )
    op.add_column("clients", sa.Column("employee_count", sa.Integer(), nullable=True))
    op.add_column("clients", sa.Column("founded_year", sa.Integer(), nullable=True))
    op.add_column("clients", sa.Column("revenue_band", sa.String(length=60), nullable=True))
    op.add_column(
        "clients",
        sa.Column("revenue_trend", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_index("ix_clients_sector", "clients", ["sector"])

    # advisor_notes
    op.create_table(
        "advisor_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("advisor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["advisor_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_advisor_notes_client_id", "advisor_notes", ["client_id"])
    op.create_index("ix_advisor_notes_advisor_id", "advisor_notes", ["advisor_id"])
    op.create_index("ix_advisor_notes_created_at", "advisor_notes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_advisor_notes_created_at", table_name="advisor_notes")
    op.drop_index("ix_advisor_notes_advisor_id", table_name="advisor_notes")
    op.drop_index("ix_advisor_notes_client_id", table_name="advisor_notes")
    op.drop_table("advisor_notes")

    op.drop_index("ix_clients_sector", table_name="clients")
    op.drop_column("clients", "revenue_trend")
    op.drop_column("clients", "revenue_band")
    op.drop_column("clients", "founded_year")
    op.drop_column("clients", "employee_count")
    op.drop_column("clients", "business_size")
    sa.Enum(name="business_size").drop(op.get_bind(), checkfirst=True)
