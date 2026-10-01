import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class DiagnosticProgress(BaseModel):
    stage: str
    label: str
    snapshot_done: int = 0
    snapshot_total: int = 0
    scan_done: int = 0
    scan_total: int = 0
    finance_done: int = 0
    finance_total: int = 0
    branch_done: int = 0
    branch_total: int = 0
    triangulate_done: int = 0
    triangulate_total: int = 0


class DiagnosticTurnOut(BaseModel):
    """Returned from /start and /message - the latest assistant message plus stage."""
    session_id: uuid.UUID
    message: ChatMessageOut
    is_complete: bool
    progress: DiagnosticProgress


class DiagnosticSessionDetail(BaseModel):
    """Full session state - used for the GET endpoint."""
    session_id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    messages: list[ChatMessageOut]
    progress: DiagnosticProgress


class UserMessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
