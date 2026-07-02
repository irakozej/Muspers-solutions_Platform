"""Diagnostic chatbot endpoints. Client-only (logged-in clients drive the
interview from the /diagnostic page in the frontend)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user, require_role
from app.core.limiter import limiter, user_or_ip_key
from app.db.session import get_db
from app.models.diagnostic_session import DiagnosticSession, SessionStatus
from app.models.user import User, UserRole
from app.schemas.diagnostic import (
    ChatMessageOut,
    DiagnosticSessionDetail,
    DiagnosticTurnOut,
    UserMessageIn,
)
from app.services import dashboard as dash_svc
from app.services import diagnostic_chatbot as chatbot

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])


def _require_client_profile(db: Session, user: User):
    client = dash_svc.get_client_for_user(db, user)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No client profile is attached to this account.",
        )
    return client


def _load_session_for_user(
    db: Session, *, session_id: uuid.UUID, user: User
) -> DiagnosticSession:
    client = _require_client_profile(db, user)
    session = db.scalar(
        select(DiagnosticSession)
        .options(selectinload(DiagnosticSession.messages))
        .where(DiagnosticSession.id == session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This session does not belong to your account.",
        )
    return session


@router.post(
    "/start",
    response_model=DiagnosticTurnOut,
    status_code=status.HTTP_201_CREATED,
)
# 5 new interviews per hour per user: prevents session-spam while letting a
# genuine client restart after a typo or an interruption.
@limiter.limit("5/hour", key_func=user_or_ip_key)
def start_diagnostic(
    request: Request,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> DiagnosticTurnOut:
    client = _require_client_profile(db, user)
    session, assistant_msg = chatbot.start_session(db, client_id=client.id)
    return DiagnosticTurnOut(
        session_id=session.id,
        message=ChatMessageOut.model_validate(assistant_msg),
        is_complete=False,
        progress=chatbot.session_progress(session.diagnostic_state),
    )


@router.post("/{session_id}/message", response_model=DiagnosticTurnOut)
# 20 messages per minute per user: comfortably above human typing speed
# (a turn every 3 seconds), well below scripted-flooding speed.
@limiter.limit("20/minute", key_func=user_or_ip_key)
def post_message(
    request: Request,
    session_id: uuid.UUID,
    payload: UserMessageIn,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> DiagnosticTurnOut:
    session = _load_session_for_user(db, session_id=session_id, user=user)
    _, assistant_msg, is_complete = chatbot.submit_user_message(
        db, session=session, content=payload.content
    )
    return DiagnosticTurnOut(
        session_id=session.id,
        message=ChatMessageOut.model_validate(assistant_msg),
        is_complete=is_complete,
        progress=chatbot.session_progress(session.diagnostic_state),
    )


@router.get("/{session_id}", response_model=DiagnosticSessionDetail)
def get_session(
    session_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> DiagnosticSessionDetail:
    session = _load_session_for_user(db, session_id=session_id, user=user)
    messages = sorted(session.messages, key=lambda m: m.created_at)
    return DiagnosticSessionDetail(
        session_id=session.id,
        status=session.status.value,
        started_at=session.started_at,
        completed_at=session.completed_at,
        messages=[ChatMessageOut.model_validate(m) for m in messages],
        progress=chatbot.session_progress(session.diagnostic_state),
    )
