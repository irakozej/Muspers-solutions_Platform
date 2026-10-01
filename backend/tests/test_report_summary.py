"""Summary-first report: headline scores, bands, priorities, payload privacy,
old-report fallbacks and PDF rendering. No Claude calls."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.core.scoring import BAND_LABELS, band_label
from app.db.session import SessionLocal
from app.models.diagnostic_session import SessionStatus
from app.services import dashboard as dash
from app.services import pdf_report
from app.services import report_generator as rg
from app.services import report_summary as rs

from tests.test_money_habits import _completed_state
from tests.test_report_scan_sections import _fake_analysis, _generate


def _scan(**scores):
    return {k: {"score": v} for k, v in scores.items()}


def _fin(**scores):
    return {k: {"score": v} for k, v in scores.items()}


def test_business_health_rescales_scan_to_0_100():
    assert rs.business_health_pct(_scan(A=5, B=5, C=5, D=5, E=5, F=5)) == 100
    assert rs.business_health_pct(_scan(A=1, B=1, C=1, D=1, E=1, F=1)) == 0
    # avg 3.5 -> (2.5 / 4) x 100 = 62.5 -> 63 (half up)
    assert rs.business_health_pct(_scan(A=5, B=4, C=2, D=1, E=4, F=5)) == 63
    assert rs.business_health_pct({}) is None


def test_band_labels_live_in_one_config_place():
    assert BAND_LABELS == {"A": "Strong footing", "B": "Building", "C": "Foundations first"}
    assert band_label(None) == "Not assessed"
    summary = rs.build_summary({"financial_health_pct": 80, "scan": _scan(A=3)}, {})
    assert summary["financial_health"]["band"] == "A"
    assert summary["financial_health"]["band_label"] == "Strong footing"


def test_priorities_two_or_three_weakest_finance_first_on_ties():
    scan = _scan(A=1, B=2, C=4, D=3, E=5, F=2)  # A=0%, B=25%, F=25%
    finance = _fin(awareness=0, cash_flow=1, pricing=3, debt=2,
                   reserves=1, growth=3, mindset=2, compliance=3)  # 0%, 33%, 33%
    got = [(p["kind"], p["key"]) for p in rs.priority_areas(scan, finance)]
    # 0%: awareness (finance) ties with A (scan) -> finance first. Then B at 25%.
    assert got == [("finance", "awareness"), ("scan", "A"), ("scan", "B")]
    assert rs.priority_areas(scan, finance)[0]["recommendation"].startswith("Set up basic bookkeeping")


def test_priorities_skip_areas_that_are_not_weak():
    assert rs.priority_areas(_scan(A=3, B=4), _fin(awareness=2, debt=3)) == []


def test_strongest_and_weakest_span_scan_and_finance():
    s = rs.build_summary({"scan": _scan(A=4, B=2), "finance": _fin(debt=3, awareness=0)}, {})
    assert (s["strongest"]["kind"], s["strongest"]["key"]) == ("finance", "debt")
    assert (s["weakest"]["kind"], s["weakest"]["key"]) == ("finance", "awareness")


def test_new_report_has_cover_priorities_and_money_habits(monkeypatch):
    state = _completed_state()
    captured = {}

    def fake_model(evidence, tool):
        captured["tool"] = tool
        captured["evidence"] = evidence
        a = _fake_analysis({})
        a["combined_headline"] = "Money habits are the floor — everything stands on it. 🚩"
        a["combined_body"] = "One. Two - with a dash. Three. Four. Five."
        a["finance_summaries"] = {"awareness": "Knows little about last month."}
        a["priority_steps"] = {"awareness": "Open a spreadsheet today."}
        return a

    monkeypatch.setattr(rg, "_call_report_model", fake_model)
    db = MagicMock()
    db.scalar.return_value = None
    session = SimpleNamespace(id=uuid.uuid4(), status=SessionStatus.completed,
                              diagnostic_state=state, messages=[])
    report = rg.generate_report(db, session)
    report.id, report.is_shared, report.created_at = uuid.uuid4(), True, datetime.now(timezone.utc)

    props = captured["tool"]["input_schema"]["properties"]
    assert {"combined_headline", "combined_body", "finance_summaries", "priority_steps"} <= set(props)
    assert "Priority areas, weakest first" in captured["evidence"]
    assert "Financial Health: 71%" in captured["evidence"]

    combined = report.content_json["combined"]
    assert "—" not in combined["headline"] and "🚩" not in combined["headline"]
    assert combined["body"] == "One. Two, with a dash. Three."  # capped at 3 sentences, dash softened
    # Scan D=1 (0%), C=2 (25%), then awareness=1 (33%, ties debt; framework order wins).
    prios = report.content_json["priorities"]
    assert [p["key"] for p in prios] == ["D", "C", "awareness"]
    assert prios[2]["first_step"] == "Open a spreadsheet today."
    assert prios[0]["first_step"]  # model gave none for D: falls back, never empty

    client_view = dash._report_payload(report, session_id=session.id)
    cover = client_view["summary_cover"]
    assert cover["financial_health"] == {"pct": 71, "assessed": True, "band": "B", "band_label": "Building"}
    assert cover["business_health"]["pct"] == 54  # Scan avg 3.17 -> (2.17 / 4) x 100
    assert len(client_view["money_habits"]) == 8
    assert client_view["money_habits"][0]["summary"] == "Knows little about last month."
    assert client_view["money_habits"][0]["recommendation"]
    assert client_view["financial_health_row"]["key"] == "G"
    assert [s["title"] for s in client_view["next_steps"]] == [
        "Read and reflect", "Pick one action to start this week", "Book a session with Penny",
    ]
    assert "rationale" not in json.dumps(client_view, default=str), "leak: client payload has rationales"
    advisor_view = dash._report_payload(report, session_id=session.id, include_rationales=True)
    assert advisor_view["money_habits"][2]["rationale"] == "PRIVATE pricing"
    assert "rationale" in advisor_view["scan_results"]["A"]  # key reaches the advisor (None in this fixture)

    pdf, _ = pdf_report.render_report_pdf(client={"business_name": "Test Co"}, report=advisor_view)
    assert pdf.startswith(b"%PDF")


def test_old_report_without_finance_renders_not_assessed(monkeypatch):
    state = _completed_state()
    for key in ("finance", "finance_idx", "finance_phase", "finance_followups"):
        state.pop(key)
    report, sid = _generate(monkeypatch, state, {})
    # Simulate a report saved before Task C: no combined statement, no priorities.
    report.content_json = {k: v for k, v in report.content_json.items() if k not in ("combined", "priorities")}

    view = dash._report_payload(report, session_id=sid)
    cover = view["summary_cover"]
    assert cover["financial_health"] == {"pct": None, "assessed": False, "band": None, "band_label": "Not assessed"}
    assert cover["combined"]["headline"] == report.content_json["summary"]  # headline stands in
    assert view["priorities"] == []
    assert all(m["score"] is None for m in view["money_habits"])
    assert view["financial_health_row"]["assessed"] is False
    pdf, _ = pdf_report.render_report_pdf(client={"business_name": "Old Co"}, report=view)
    assert pdf.startswith(b"%PDF")


def test_sanitize_strips_dashes_and_emoji():
    out = rg._sanitize({"a": ["Cash is tight — very tight 🚩", "Plan – act", "Fix it - now", "3-4 weeks"]})
    assert out["a"] == ["Cash is tight, very tight", "Plan, act", "Fix it, now", "3-4 weeks"]


def test_advisor_analytics_has_financial_health_averages():
    db = SessionLocal()
    try:
        data = dash.collect_analytics(db)
    finally:
        db.close()
    assert "average_financial_health" in data
    assert [c["key"] for c in data["average_finance_scores"]] == [
        "awareness", "cash_flow", "pricing", "debt", "reserves", "growth", "mindset", "compliance",
    ]
