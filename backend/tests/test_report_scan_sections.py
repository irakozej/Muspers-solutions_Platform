"""Regression tests: every Scan area (A-F) always reaches the report with data.

Covers the empty-Scan-section bug: an off-topic turn during Scan used to
advance the state with no score and no answer, leaving that area blank and
filing every later answer one area too late. No real Claude calls.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from reportlab.platypus import KeepTogether, Paragraph

from app.models.diagnostic_session import SessionStatus
from app.services import dashboard as dash
from app.services import diagnostic_chatbot as cb
from app.services import pdf_report
from app.services import report_generator as rg

from tests.test_diagnostic_hardening import FAKE_FIRST, _auth, _register_client_user, _start

SCORES = {"A": 5, "B": 2, "C": 4, "D": 2, "E": 4, "F": 1}


def _scan_state():
    state = cb.init_state()
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    return state


def _answer(key):
    return {
        "status": "answered",
        "extracted_value": f"client answer for {key}",
        "score": SCORES[key],
        "score_rationale": f"PRIVATE note for {key}",
    }


# ───────────────────── state machine ─────────────────────

def test_empty_scan_turn_does_not_advance_or_shift_later_answers():
    """An off-topic reply recorded as 'answered' with nothing in it must not
    consume the area: the model re-asks the same question."""
    state = _scan_state()
    target = cb.next_target(state)  # A
    advanced = cb.apply_extraction(state, target, {"status": "answered", "extracted_value": ""})
    assert advanced is False
    assert cb.next_target(state)["area"]["key"] == "A"

    for key in cb.SCAN_AREA_KEYS:
        target = cb.next_target(state)
        assert target["area"]["key"] == key
        cb.apply_extraction(state, target, _answer(key))

    for key in cb.SCAN_AREA_KEYS:
        assert state["scan"][key]["score"] == SCORES[key]
        assert state["scan"][key]["answer"] == f"client answer for {key}"


def test_missing_tool_call_during_scan_does_not_advance():
    state = _scan_state()
    target = cb.next_target(state)
    assert cb.apply_extraction(state, target, {"status": "answered"}) is False
    assert state["scan_area_idx"] == 0


def test_second_empty_scan_turn_defaults_to_three_and_is_flagged():
    state = _scan_state()
    target = cb.next_target(state)
    cb.apply_extraction(state, target, {"status": "needs_clarification"})
    assert cb.apply_extraction(state, target, {"status": "answered", "extracted_value": ""}) is True
    assert state["scan"]["A"]["score"] == 3
    assert state["scan"]["A"]["defaulted"] is True
    assert cb.next_target(state)["area"]["key"] == "B"


def test_answer_without_score_defaults_to_three_instead_of_none():
    state = _scan_state()
    target = cb.next_target(state)
    cb.apply_extraction(state, target, {"status": "answered", "extracted_value": "We have a plan."})
    assert state["scan"]["A"]["score"] == 3
    assert state["scan"]["A"]["defaulted"] is True
    assert state["scan"]["A"]["answer"] == "We have a plan."


def test_forced_advance_replaces_stale_reask_with_real_next_question(client, monkeypatch):
    """When the model asks to clarify but the backend moves on anyway, the
    reply must ask the backend's next question, not re-ask the old one."""
    token = _register_client_user(client, "forced@test.musper.com")
    sid = _start(client, token, monkeypatch)
    monkeypatch.setattr(
        cb, "_call_claude",
        lambda **_kw: (FAKE_FIRST, {"status": "needs_clarification", "extracted_value": "Inyange Foods",
                                    "snapshot": {"company_name": "Inyange Foods"}}),
    )
    r = client.post(f"/api/diagnostic/{sid}/message", headers=_auth(token), json={"content": "Inyange Foods"})
    assert r.status_code == 200, r.text
    assert r.json()["message"]["content"] == cb._fallback_next_question(
        {"stage": "snapshot", "step": cb.SNAPSHOT_STEPS[1]}
    )


# ───────────────────── report generation + rendering ─────────────────────

def _completed_state_with_one_default():
    """A full Scan where area C used the clarification-default path."""
    state = _scan_state()
    for key in cb.SCAN_AREA_KEYS:
        target = cb.next_target(state)
        if key == "C":
            cb.apply_extraction(state, target, {"status": "needs_clarification"})
            cb.apply_extraction(state, target, {"status": "needs_clarification"})
        else:
            cb.apply_extraction(state, target, _answer(key))
    state["snapshot"]["company_name"] = "Akagera Logistics"
    return state


def _fake_analysis(summaries):
    return {
        "headline": "Sales looks like the problem; operations is the cause.",
        "scan_summaries": summaries,
        "presenting_problem": "p", "root_cause": "r", "root_cause_evidence": ["e1", "e2"],
        "already_tried": [{"attempt": "a", "why_it_failed": "w"}], "ownership": "o",
        "service_pathway": [{"service": rg.SERVICE_LINES[0], "justification": "j"}],
        "engagement": {"type": "project", "timeline": "10 weeks", "next_step": "call"},
    }


def _generate(monkeypatch, state, summaries):
    monkeypatch.setattr(rg, "_call_report_model", lambda *_a, **_k: _fake_analysis(summaries))
    session = SimpleNamespace(
        id=uuid.uuid4(), status=SessionStatus.completed, diagnostic_state=state, messages=[]
    )
    db = MagicMock()
    db.scalar.return_value = None  # no existing report
    report = rg.generate_report(db, session)
    report.id = uuid.uuid4()
    report.is_shared = True
    report.created_at = datetime.now(timezone.utc)
    return report, session.id


def _pdf_scan_text(payload):
    flow: list = []
    pdf_report._register_fonts()
    pdf_report._append_root_cause_flow(
        flow, client={}, report=payload, styles=pdf_report._styles(), frame_w=400
    )
    blocks = [f for f in flow if isinstance(f, KeepTogether)]
    out = {}
    for block in blocks:
        bar = block._content[0]
        if isinstance(bar, pdf_report.ScanBar):
            out[bar.area_key] = (bar.label, bar.score, [p.text for p in block._content[1:] if isinstance(p, Paragraph)])
    return out


def test_report_from_clarification_default_renders_all_six_areas(monkeypatch):
    state = _completed_state_with_one_default()
    assert state["scan"]["C"]["answer"] == ""  # the default path stores no answer

    # The model covers five areas; C falls through to the plain-language fallback.
    summaries = {k: f"Summary of what the client said about {k}." for k in cb.SCAN_AREA_KEYS if k != "C"}
    report, sid = _generate(monkeypatch, state, summaries)

    client_view = dash._report_payload(report, session_id=sid)
    advisor_view = dash._report_payload(report, session_id=sid, include_rationales=True)

    scan = client_view["scan_results"]
    assert sorted(scan) == cb.SCAN_AREA_KEYS
    for key in cb.SCAN_AREA_KEYS:
        area = scan[key]
        assert area["name"] == cb.SCAN_AREA_MAP[key]["name"]
        assert area["score"] is not None
        assert area["summary"].strip()
        assert "rationale" not in area, f"leak: client sees rationale for {key}"
        assert "—" not in area["summary"] + (area["note"] or "")

    assert scan["C"]["score"] == 3
    assert scan["C"]["defaulted"] is True
    assert scan["C"]["summary"] == rg.NO_SUMMARY
    assert "unclear" in scan["C"]["note"]
    assert scan["A"]["note"] is None
    assert advisor_view["scan_results"]["A"]["rationale"] == "PRIVATE note for A"

    pdf = _pdf_scan_text(client_view)
    assert sorted(pdf) == cb.SCAN_AREA_KEYS
    for key, (label, score, texts) in pdf.items():
        assert label == cb.SCAN_AREA_MAP[key]["name"]
        assert score is not None
        assert texts and texts[0].strip()
    assert any("unclear" in t for t in pdf["C"][2])


def test_legacy_state_with_missing_scores_still_renders_every_area(monkeypatch):
    """States saved before the fix (null score, empty answer, no flag)."""
    state = _completed_state_with_one_default()
    for key in ("A", "D"):
        state["scan"][key] = {"score": None, "answer": "", "rationale": None, "clarified": False}
    report, sid = _generate(monkeypatch, state, {})

    scan = dash._report_payload(report, session_id=sid)["scan_results"]
    for key in cb.SCAN_AREA_KEYS:
        assert scan[key]["score"] is not None
        assert scan[key]["summary"].strip()
    assert scan["A"]["defaulted"] and scan["D"]["defaulted"]
    assert scan["B"]["summary"] == "client answer for B"  # falls back to the stored answer
