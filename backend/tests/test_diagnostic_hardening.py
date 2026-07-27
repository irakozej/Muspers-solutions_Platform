"""Security and robustness tests for the diagnostic chatbot endpoints.

All Claude calls are monkeypatched; these tests exercise the HTTP surface,
ownership checks, the turn cap, upstream-failure atomicity, and rate limits.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException

from app.core.limiter import limiter
from app.db.session import SessionLocal
from app.models.client import Client
from app.services import diagnostic_chatbot as chatbot

FAKE_FIRST = "Welcome. To start, what is the name of the business?"
FAKE_NEXT = "Noted. What sector or industry is the business in?"


def _fake_claude_ok(**_kw):
    return FAKE_NEXT, {
        "status": "answered",
        "extracted_value": "Test Co",
        "snapshot": {"company_name": "Test Co"},
    }


def _register_client_user(client, email: str) -> str:
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Password123!", "full_name": "Test Client"},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    # Registration creates the User; attach the Client profile row it needs.
    db = SessionLocal()
    try:
        db.add(Client(user_id=uuid.UUID(data["user"]["id"]), business_name="Test Co"))
        db.commit()
    finally:
        db.close()
    return data["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _start(client, token: str, monkeypatch) -> str:
    monkeypatch.setattr(chatbot, "_call_claude", lambda **_kw: (FAKE_FIRST, None))
    r = client.post("/api/diagnostic/start", headers=_auth(token))
    assert r.status_code == 201, r.text
    return r.json()["session_id"]


# ───────────────────── input validation ─────────────────────

def test_over_long_message_is_rejected(client, monkeypatch):
    token = _register_client_user(client, "longmsg@test.musper.com")
    sid = _start(client, token, monkeypatch)
    r = client.post(
        f"/api/diagnostic/{sid}/message",
        headers=_auth(token),
        json={"content": "x" * 4001},
    )
    assert r.status_code == 422


def test_empty_message_is_rejected(client, monkeypatch):
    token = _register_client_user(client, "emptymsg@test.musper.com")
    sid = _start(client, token, monkeypatch)
    r = client.post(
        f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": ""}
    )
    assert r.status_code == 422


# ───────────────────── ownership ─────────────────────

def test_client_cannot_touch_another_clients_session(client, monkeypatch):
    token_a = _register_client_user(client, "owner-a@test.musper.com")
    sid_a = _start(client, token_a, monkeypatch)

    token_b = _register_client_user(client, "owner-b@test.musper.com")
    # B cannot read A's session
    r = client.get(f"/api/diagnostic/{sid_a}", headers=_auth(token_b))
    assert r.status_code == 403
    # B cannot post into A's session
    r = client.post(
        f"/api/diagnostic/{sid_a}/message", headers=_auth(token_b), json={"content": "hi"}
    )
    assert r.status_code == 403


# ───────────────────── turn cap ─────────────────────

def test_turn_cap_closes_gracefully_without_calling_claude(client, monkeypatch):
    token = _register_client_user(client, "turncap@test.musper.com")
    sid = _start(client, token, monkeypatch)

    monkeypatch.setattr(chatbot.settings, "diagnostic_max_user_turns", 2)
    monkeypatch.setattr(chatbot, "_call_claude", lambda **_kw: _fake_claude_ok())

    # Turns 1 and 2 are under the cap and go through the (mocked) model.
    for i in range(2):
        r = client.post(
            f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": f"turn {i}"}
        )
        assert r.status_code == 200
        assert r.json()["is_complete"] is False

    # Turn 3 hits the cap. If the model were called this would raise.
    def _explode(**_kw):
        raise AssertionError("Claude must not be called on the turn-cap path")

    monkeypatch.setattr(chatbot, "_call_claude", _explode)
    r = client.post(
        f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": "turn 3"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["is_complete"] is True
    assert "MusperSolutions" in body["message"]["content"]

    # Session is completed; further messages are rejected.
    r = client.get(f"/api/diagnostic/{sid}", headers=_auth(token))
    assert r.json()["status"] == "completed"
    r = client.post(
        f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": "more"}
    )
    assert r.status_code == 409


# ───────────────────── upstream failure atomicity ─────────────────────

def test_upstream_failure_is_atomic_and_retryable(client, monkeypatch):
    token = _register_client_user(client, "atomic@test.musper.com")
    sid = _start(client, token, monkeypatch)

    def _fail(**_kw):
        raise HTTPException(status_code=503, detail=chatbot._RETRY_MSG)

    monkeypatch.setattr(chatbot, "_call_claude", _fail)
    r = client.post(
        f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": "Inyange Foods"}
    )
    assert r.status_code == 503
    # Friendly message only; no upstream internals, no secrets.
    detail = r.json()["detail"]
    assert "sk-ant" not in detail
    assert "billing" not in detail.lower()
    assert "send the same answer again" in detail

    # State untouched: only the opening assistant message exists, still in progress.
    r = client.get(f"/api/diagnostic/{sid}", headers=_auth(token))
    body = r.json()
    assert body["status"] == "in_progress"
    assert len(body["messages"]) == 1
    assert body["progress"]["snapshot_done"] == 0

    # Retry with the model healthy: the same answer now advances state once.
    monkeypatch.setattr(chatbot, "_call_claude", lambda **_kw: _fake_claude_ok())
    r = client.post(
        f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": "Inyange Foods"}
    )
    assert r.status_code == 200
    r = client.get(f"/api/diagnostic/{sid}", headers=_auth(token))
    body = r.json()
    assert len(body["messages"]) == 3  # opening + user + assistant
    assert body["progress"]["snapshot_done"] == 1


# ───────────────────── rate limits ─────────────────────

def test_start_rate_limit_5_per_hour(client, monkeypatch):
    token = _register_client_user(client, "ratestart@test.musper.com")
    monkeypatch.setattr(chatbot, "_call_claude", lambda **_kw: (FAKE_FIRST, None))
    limiter.enabled = True
    try:
        for _ in range(5):
            r = client.post("/api/diagnostic/start", headers=_auth(token))
            assert r.status_code == 201
        r = client.post("/api/diagnostic/start", headers=_auth(token))
        assert r.status_code == 429
    finally:
        limiter.enabled = False


def test_message_rate_limit_20_per_minute(client, monkeypatch):
    token = _register_client_user(client, "ratemsg@test.musper.com")
    sid = _start(client, token, monkeypatch)
    monkeypatch.setattr(chatbot, "_call_claude", lambda **_kw: _fake_claude_ok())
    limiter.enabled = True
    try:
        # The mocked interview completes naturally around turn 17, after which
        # the endpoint returns 409 (already completed). The limiter counts every
        # request regardless, so the first 20 must never be rate-limited and
        # the 21st must be.
        for i in range(20):
            r = client.post(
                f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": f"m{i}"}
            )
            assert r.status_code in (200, 409), f"turn {i}: {r.text}"
            assert r.status_code != 429, f"rate limit fired too early on turn {i}"
        r = client.post(
            f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": "over"}
        )
        assert r.status_code == 429
    finally:
        limiter.enabled = False


def test_rate_limit_keys_are_per_user_not_shared(client, monkeypatch):
    """Two different users must not share a rate bucket."""
    token_a = _register_client_user(client, "bucket-a@test.musper.com")
    token_b = _register_client_user(client, "bucket-b@test.musper.com")
    monkeypatch.setattr(chatbot, "_call_claude", lambda **_kw: (FAKE_FIRST, None))
    limiter.enabled = True
    try:
        for _ in range(5):
            assert client.post("/api/diagnostic/start", headers=_auth(token_a)).status_code == 201
        # A is now limited; B still is not.
        assert client.post("/api/diagnostic/start", headers=_auth(token_a)).status_code == 429
        assert client.post("/api/diagnostic/start", headers=_auth(token_b)).status_code == 201
    finally:
        limiter.enabled = False


# ───────────────────── rationale leak (audit finding) ─────────────────────

def test_client_report_payload_excludes_rationales_advisor_includes():
    """Scan rationales are the interviewer's private scoring notes. They must
    reach the advisor payload but never the client payload, even though the
    client UI hides them."""
    from types import SimpleNamespace
    from datetime import datetime, timezone
    from app.services import dashboard as dash

    fake = SimpleNamespace(
        id=uuid.uuid4(),
        is_shared=True,
        created_at=datetime.now(timezone.utc),
        scores_json={
            "report_type": "root_cause",
            "scan": {"A": {"name": "Strategic Clarity", "score": 2,
                           "rationale": "PRIVATE: weak strategy signals"}},
            "grow_overall": 40, "grow_band": "C",
            "finance_readiness": 40, "finance_band": "C",
        },
        content_json={"report_type": "root_cause", "summary": "s",
                      "diagnosis": {}, "service_pathway": [], "engagement": {},
                      "snapshot": {}},
    )
    sid = uuid.uuid4()

    client_view = dash._report_payload(fake, session_id=sid)
    advisor_view = dash._report_payload(fake, session_id=sid, include_rationales=True)

    assert "rationale" not in client_view["scan_results"]["A"], "leak: client sees rationale"
    assert client_view["scan_results"]["A"]["score"] == 2  # score still shown
    assert advisor_view["scan_results"]["A"]["rationale"] == "PRIVATE: weak strategy signals"
