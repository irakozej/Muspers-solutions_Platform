"""Regression: a turn's user message and reply sharing one timestamp must
never reorder the model history (the API rejects non-alternating roles, and
the session would be stuck on every retry)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.chat_message import ChatMessage, MessageRole
from app.models.client import Client
from app.models.diagnostic_session import DiagnosticSession, SessionStatus
from app.models.user import User
from app.services import diagnostic_chatbot as cb

from tests.test_diagnostic_hardening import _register_client_user


def test_tied_timestamps_keep_user_before_reply_in_model_history(client, monkeypatch):
    _register_client_user(client, "tie@test.musper.com")
    db = SessionLocal()
    try:
        c = db.scalar(select(Client).join(User).where(User.email == "tie@test.musper.com"))
        state = cb.init_state()
        state["current_target"] = cb.next_target(state)
        session = DiagnosticSession(client_id=c.id, status=SessionStatus.in_progress, diagnostic_state=state)
        db.add(session)
        db.flush()
        t0 = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 10, 1, 9, 1, tzinfo=timezone.utc)
        # Opening question, then one turn saved in a single transaction (same
        # timestamp). The reply gets the smaller UUID so a naive sort puts it first.
        db.add(ChatMessage(session_id=session.id, role=MessageRole.assistant, content="Name?", created_at=t0))
        db.add(ChatMessage(id=uuid.UUID(int=1), session_id=session.id, role=MessageRole.assistant,
                           content="What sector?", created_at=t1))
        db.add(ChatMessage(id=uuid.UUID(int=2), session_id=session.id, role=MessageRole.user,
                           content="Inyange Foods", created_at=t1))
        db.commit()

        captured = {}

        def fake_claude(*, system_prompt, history):
            captured["history"] = history
            return "Noted. How long has the business been operating?", {
                "status": "answered", "snapshot": {"sector": "Agro-processing"}}

        monkeypatch.setattr(cb, "_call_claude", fake_claude)
        db.refresh(session)
        cb.submit_user_message(db, session=session, content="Agro-processing")

        roles = [m["role"] for m in captured["history"]]
        assert roles == ["assistant", "user", "assistant", "user"], roles
        assert [m["content"] for m in captured["history"]][1:3] == ["Inyange Foods", "What sector?"]

        # New rows get distinct Python-side timestamps, user strictly first.
        rows = sorted(db.scalars(select(ChatMessage).where(ChatMessage.session_id == session.id)),
                      key=lambda m: m.created_at)
        assert rows[-2].role == MessageRole.user and rows[-2].created_at < rows[-1].created_at
    finally:
        db.close()
