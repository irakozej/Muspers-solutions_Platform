"""Client teaser snapshot and the share gate, exercised over HTTP.

The teaser is the only analysis a client can reach before Penny shares the
report; everything else (root cause, recommendations, rationales,
per-category scores) stays server-side until she does.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal
from app.main import app
from app.models.client import Client
from app.models.diagnostic_session import DiagnosticSession, SessionStatus
from app.models.report import Report
from app.models.user import User, UserRole
from app.services import report_generator as rg

from tests.conftest import csrf_headers
from tests.test_diagnostic_hardening import _auth, _register_client_user
from tests.test_money_habits import _completed_state
from tests.test_report_scan_sections import _fake_analysis

ALLOWED_KEYS = {
    "session_id", "completed_at", "financial_health", "business_health",
    "strongest_area", "attention_area", "locked_sections", "share_note",
    "report_shared", "report_id",
}
SCORE_KEYS = {"pct", "band", "band_label", "assessed"}


def _completed_session_with_report(email_token: str, *, state=None) -> tuple[str, str]:
    """Create a completed interview + its (unshared) report for the client
    behind this token. Returns (session_id, report_id)."""
    state = state or _completed_state()
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email_token))
        client = db.scalar(select(Client).where(Client.user_id == user.id))
        session = DiagnosticSession(
            client_id=client.id, status=SessionStatus.completed,
            diagnostic_state=state, completed_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.flush()
        analysis = _fake_analysis({"A": "Strategy summary"})
        analysis["combined_body"] = "SECRET ROOT CAUSE TEXT."
        report = Report(
            session_id=session.id,
            scores_json=rg._scores_json(state),
            content_json=rg._content_json(state, analysis, []),
        )
        db.add(report)
        db.commit()
        return str(session.id), str(report.id)
    finally:
        db.close()


def _advisor_client() -> TestClient:
    """A logged-in advisor (Penny) with CSRF cookies, on its own client."""
    c = TestClient(app)
    email = f"penny-{uuid.uuid4().hex[:6]}@test.musper.com"
    r = c.post("/api/auth/register", json={"email": email, "password": "Password123!", "full_name": "Penny"})
    assert r.status_code == 201, r.text
    db = SessionLocal()
    try:
        u = db.scalar(select(User).where(User.email == email))
        u.role = UserRole.advisor
        db.commit()
    finally:
        db.close()
    r = c.post("/api/auth/login", json={"email": email, "password": "Password123!"})
    assert r.status_code == 200, r.text
    c.headers.update(_auth(r.json()["access_token"]))
    return c


def test_snapshot_contains_only_allowlisted_keys(client):
    token = _register_client_user(client, "teaser@test.musper.com")
    sid, _ = _completed_session_with_report("teaser@test.musper.com")

    r = client.get(f"/api/client/sessions/{sid}/snapshot", headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == ALLOWED_KEYS
    assert set(body["financial_health"]) == SCORE_KEYS == set(body["business_health"])
    assert body["financial_health"] == {"pct": 71, "band": "B", "band_label": "Building", "assessed": True}
    assert isinstance(body["strongest_area"], str) and isinstance(body["attention_area"], str)
    assert body["locked_sections"] == ["Money habits breakdown", "Root cause diagnosis",
                                       "Priority actions", "Recommendations"]
    assert body["report_shared"] is False and body["report_id"] is None

    # Scan everything except the locked section TITLES (which name, not reveal, content).
    raw = json.dumps({k: v for k, v in body.items() if k != "locked_sections"}).lower()
    for forbidden in ("rationale", "root_cause", "recommendation\"", "secret root cause",
                      "private", "summary\"", "awareness", "cash_flow", "scan_results",
                      "money_habits", "priorities", "first_step", "diagnosis"):
        assert forbidden not in raw, f"teaser leaks {forbidden!r}"


def test_snapshot_of_another_clients_session_is_403(client):
    _register_client_user(client, "owner@test.musper.com")
    sid, _ = _completed_session_with_report("owner@test.musper.com")
    other = TestClient(app)
    other_token = _register_client_user(other, "intruder@test.musper.com")
    r = other.get(f"/api/client/sessions/{sid}/snapshot", headers=_auth(other_token))
    assert r.status_code == 403
    assert "Building" not in r.text


def test_snapshot_waits_for_completion(client):
    token = _register_client_user(client, "early@test.musper.com")
    sid, _ = _completed_session_with_report("early@test.musper.com")
    db = SessionLocal()
    try:
        db.get(DiagnosticSession, uuid.UUID(sid)).status = SessionStatus.in_progress
        db.commit()
    finally:
        db.close()
    assert client.get(f"/api/client/sessions/{sid}/snapshot", headers=_auth(token)).status_code == 409


def test_full_report_locked_until_shared_then_unlocked(client):
    token = _register_client_user(client, "share@test.musper.com")
    sid, rid = _completed_session_with_report("share@test.musper.com")
    h = _auth(token)

    # Locked: single report, PDF, report list, and the session list's scores.
    assert client.get(f"/api/client/reports/{rid}", headers=h).status_code == 403
    assert client.get(f"/api/client/reports/{rid}/report.pdf", headers=h).status_code == 403
    assert client.get("/api/client/reports", headers=h).json() == []
    me = client.get("/api/client/me", headers=h).json()
    assert me["shared_reports"] == []
    session_row = next(s for s in me["sessions"] if s["id"] == sid)
    assert session_row["overall_score"] is None and session_row["band"] is None
    assert "SECRET ROOT CAUSE" not in json.dumps(me)

    # Penny shares through the real advisor endpoint (CSRF and all).
    penny = _advisor_client()
    r = penny.patch(f"/api/advisor/reports/{rid}/share", json={"is_shared": True}, headers=csrf_headers(penny))
    assert r.status_code == 200, r.text

    r = client.get(f"/api/client/reports/{rid}", headers=h)
    assert r.status_code == 200
    full = r.json()
    assert full["summary_cover"]["combined"]["body"] == "SECRET ROOT CAUSE TEXT."
    assert len(full["money_habits"]) == 8
    assert "rationale" not in json.dumps(full), "client report must never carry rationales"
    pdf = client.get(f"/api/client/reports/{rid}/report.pdf", headers=h)
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")
    teaser = client.get(f"/api/client/sessions/{sid}/snapshot", headers=h).json()
    assert teaser["report_shared"] is True and teaser["report_id"] == rid  # teaser stays visible
    assert next(s for s in client.get("/api/client/sessions", headers=h).json() if s["id"] == sid)["overall_score"] is not None


def test_another_clients_shared_report_is_403(client):
    _register_client_user(client, "a@test.musper.com")
    _, rid = _completed_session_with_report("a@test.musper.com")
    db = SessionLocal()
    try:
        db.get(Report, uuid.UUID(rid)).is_shared = True
        db.commit()
    finally:
        db.close()
    other = TestClient(app)
    tok = _register_client_user(other, "b@test.musper.com")
    assert other.get(f"/api/client/reports/{rid}", headers=_auth(tok)).status_code == 403


def test_teaser_for_session_without_scan_data_is_not_assessed(client):
    token = _register_client_user(client, "legacy@test.musper.com")
    from app.services.diagnostic_chatbot import init_state
    state = init_state()
    state["stage"] = "complete"
    sid, _ = _completed_session_with_report("legacy@test.musper.com", state=state)
    body = client.get(f"/api/client/sessions/{sid}/snapshot", headers=_auth(token)).json()
    assert body["business_health"]["assessed"] is False
    assert body["financial_health"]["band_label"] == "Not assessed"
    assert body["strongest_area"] is None
