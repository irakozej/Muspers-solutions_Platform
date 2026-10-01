import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("diagnostic_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Set in Python, not by the database: Postgres now() is fixed per
    # transaction, so a turn's user message and reply (one commit) would tie.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    session: Mapped["DiagnosticSession"] = relationship(back_populates="messages")  # noqa: F821


def message_order(m: "ChatMessage") -> tuple:
    """Transcript order. Rows saved before created_at was set in Python can
    share a timestamp with the other half of their turn; a tie is always one
    turn's user message and its reply, so the user message goes first.
    Without this the model history could start with the reply, two user
    messages would end up adjacent, and the API would reject every retry."""
    return (m.created_at, 0 if m.role == MessageRole.user else 1)
