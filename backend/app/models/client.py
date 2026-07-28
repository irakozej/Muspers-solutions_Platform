import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BusinessSize(str, enum.Enum):
    micro = "micro"
    small = "small"
    medium = "medium"
    large = "large"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Nullable: a profile is created empty at signup and filled from the
    # diagnostic snapshot (or by the client editing their profile).
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)

    # Phase 6: business metadata for the dashboard
    business_size: Mapped[BusinessSize | None] = mapped_column(
        Enum(BusinessSize, name="business_size"), nullable=True
    )
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue_band: Mapped[str | None] = mapped_column(String(60), nullable=True)
    revenue_trend: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="client_profile")  # noqa: F821
    diagnostic_sessions: Mapped[list["DiagnosticSession"]] = relationship(  # noqa: F821
        back_populates="client", cascade="all, delete-orphan"
    )
    advisor_notes: Mapped[list["AdvisorNote"]] = relationship(  # noqa: F821
        back_populates="client", cascade="all, delete-orphan", order_by="AdvisorNote.created_at.desc()"
    )
