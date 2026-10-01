"""Diagnostic chatbot endpoints.

The interview endpoints are client-only (logged-in clients drive the interview
from the /diagnostic page). Report generation is advisor-only; it also fires
automatically in the background the moment an interview completes.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user, require_csrf, require_role
from app.core.limiter import limiter, user_or_ip_key
from app.db.session import get_db
from app.models.chat_message import message_order
from app.models.client import Client
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
from app.services import report_generator

router = APIRouter(prefix="/api/diagnostic", tags=["diagnostic"])

log = logging.getLogger("musper.diagnostic")


def _require_client_profile(db: Session, user: User):
    client = dash_svc.get_client_for_user(db, user)
    if client is None:
        if user.role != UserRole.client:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No client profile is attached to this account.",
            )
        # Self-heal: signup now creates the profile row, but accounts registered
        # before that fix (or a row lost some other way) land here.
        log.warning(
            "Client-role user %s had no client profile; creating a minimal one.", user.id
        )
        db.add(Client(user_id=user.id))
        db.commit()
        client = dash_svc.get_client_for_user(db, user)
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
    background_tasks: BackgroundTasks,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> DiagnosticTurnOut:
    session = _load_session_for_user(db, session_id=session_id, user=user)
    _, assistant_msg, is_complete = chatbot.submit_user_message(
        db, session=session, content=payload.content
    )
    if is_complete:
        # Auto-generate MusperSolutions' report in the background so it is waiting in
        # her dashboard, without delaying the client's completion screen.
        background_tasks.add_task(report_generator.generate_report_for_session, session.id)
    return DiagnosticTurnOut(
        session_id=session.id,
        message=ChatMessageOut.model_validate(assistant_msg),
        is_complete=is_complete,
        progress=chatbot.session_progress(session.diagnostic_state),
    )


@router.post("/{session_id}/generate-report")
# 10/hour: report generation is the most expensive single call in the system.
# Advisor-only, so this is a cost guard rather than an abuse guard.
@limiter.limit("10/hour", key_func=user_or_ip_key)
def generate_report(
    request: Request,
    session_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> dict:
    """Generate or regenerate the Root-Cause Diagnostic Report for a completed
    session. Regeneration overwrites the analysis but preserves the report's
    is_shared flag."""
    session = db.scalar(
        select(DiagnosticSession)
        .options(selectinload(DiagnosticSession.messages))
        .where(DiagnosticSession.id == session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    report = report_generator.generate_report(db, session)
    return dash_svc._report_payload(report, session_id=session.id, include_rationales=True)


@router.get("/{session_id}", response_model=DiagnosticSessionDetail)
def get_session(
    session_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> DiagnosticSessionDetail:
    session = _load_session_for_user(db, session_id=session_id, user=user)
    messages = sorted(session.messages, key=message_order)
    return DiagnosticSessionDetail(
        session_id=session.id,
        status=session.status.value,
        started_at=session.started_at,
        completed_at=session.completed_at,
        messages=[ChatMessageOut.model_validate(m) for m in messages],
        progress=chatbot.session_progress(session.diagnostic_state),
    )
