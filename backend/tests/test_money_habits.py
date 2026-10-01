"""Money Habits stage: flow, scoring, follow-up rules and report data. No Claude calls."""
from __future__ import annotations

from app.services import dashboard as dash
from app.services import diagnostic_chatbot as cb
from app.services import finance_framework as ff
from app.services import report_generator as rg

from tests.test_report_scan_sections import _generate

SCAN_SCORES = {"A": 5, "B": 4, "C": 2, "D": 1, "E": 4, "F": 3}
# Weak (0-1) on awareness, debt and growth; strong on the rest.
FINANCE_SCORES = {
    "awareness": 0, "cash_flow": 3, "pricing": 2, "debt": 1,
    "reserves": 3, "growth": 1, "mindset": 2, "compliance": 3,
}
FOLLOWUP_FINAL = {"awareness": 1, "debt": 1, "growth": 2}


def _at_money_habits():
    state = cb.init_state()
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    target = cb.next_target(state)
    for key in cb.SCAN_AREA_KEYS:
        cb.apply_extraction(state, target, {"status": "answered", "extracted_value": "...", "score": SCAN_SCORES[key]})
        target = cb.next_target(state)
    return state, target


def _run_money_habits(state, target):
    """Drive the stage, recording every question the backend asks."""
    asked = []
    while target["stage"] == "finance":
        key, phase = target["category"]["key"], target["phase"]
        asked.append((key, phase))
        if phase == "anchor":
            extraction = {"status": "answered", "extracted_value": f"{key} answer",
                          "finance_score": FINANCE_SCORES[key], "score_rationale": f"PRIVATE {key}"}
        else:
            extraction = {"status": "answered", "extracted_value": f"{key} follow-up answer",
                          "finance_score": FOLLOWUP_FINAL[key],
                          "question_asked": ff.FINANCE_MAP[key]["followups"][1]}
        cb.apply_extraction(state, target, extraction)
        target = cb.next_target(state)
    return asked, target


def test_all_eight_anchors_asked_and_followups_only_for_zero_or_one():
    state, target = _at_money_habits()
    assert target["stage"] == "finance"
    asked, target = _run_money_habits(state, target)

    assert [k for k, phase in asked if phase == "anchor"] == ff.FINANCE_KEYS
    assert [k for k, phase in asked if phase == "followup"] == ["awareness", "debt", "growth"]
    assert state["finance_followups"] == ["awareness", "debt", "growth"]
    # Each follow-up comes straight after its own anchor.
    for key in state["finance_followups"]:
        i = asked.index((key, "anchor"))
        assert asked[i + 1] == (key, "followup")

    fin = state["finance"]
    assert fin["awareness"]["score"] == 1  # finalised by the follow-up
    assert fin["growth"]["score"] == 2
    assert fin["cash_flow"]["score"] == 3
    assert fin["cash_flow"]["followup_question"] is None
    assert fin["debt"]["followup_question"] == ff.FINANCE_MAP["debt"]["followups"][1]
    assert fin["debt"]["followup_answer"] == "debt follow-up answer"
    assert fin["pricing"]["rationale"] == "PRIVATE pricing"

    # Money Habits sits between Scan and Branch; branching is unchanged.
    assert target["stage"] == "branch"
    assert state["branch_order"] == ["C", "D", "F"]


def test_finance_clarification_budget_then_unclear_scores_one():
    state, target = _at_money_habits()
    assert cb.apply_extraction(state, target, {"status": "needs_clarification"}) is False
    assert cb.next_target(state)["category"]["key"] == "awareness"
    # Still unclear: scored 1, marked unclear, and 1 earns the follow-up.
    assert cb.apply_extraction(state, target, {"status": "needs_clarification"}) is True
    assert state["finance"]["awareness"]["score"] == ff.UNCLEAR_SCORE == 1
    assert state["finance"]["awareness"]["unclear"] is True
    nxt = cb.next_target(state)
    assert (nxt["category"]["key"], nxt["phase"]) == ("awareness", "followup")
    # The follow-up does not get a second clarification.
    assert cb.apply_extraction(state, nxt, {"status": "answered", "extracted_value": ""}) is True
    assert state["finance"]["awareness"]["score"] == 1
    assert cb.next_target(state)["category"]["key"] == "cash_flow"


def test_empty_finance_turn_does_not_advance():
    state, target = _at_money_habits()
    assert cb.apply_extraction(state, target, {"status": "answered"}) is False
    assert state["finance_idx"] == 0


def test_followup_fallback_skips_question_used_in_place_of_anchor():
    state, target = _at_money_habits()
    substitute = ff.FINANCE_MAP["awareness"]["followups"][0]
    cb.apply_extraction(state, target, {"status": "answered", "extracted_value": "no idea",
                                        "finance_score": 0, "question_asked": substitute})
    assert state["finance"]["awareness"]["question"] == substitute
    assert cb._default_followup(state, "awareness") == ff.FINANCE_MAP["awareness"]["followups"][1]


def test_financial_health_pct():
    assert ff.financial_health_pct({k: 3 for k in ff.FINANCE_KEYS}) == 100
    assert ff.financial_health_pct({k: 0 for k in ff.FINANCE_KEYS}) == 0
    # 1+3+2+1+3+2+2+3 = 17 / 24 = 70.8%
    scores = {**FINANCE_SCORES, **FOLLOWUP_FINAL}
    assert sum(scores.values()) == 17
    assert ff.financial_health_pct(scores) == 71
    assert ff.financial_health_pct({**scores, "debt": None}) is None
    # Exact halves round up: 15/24 = 62.5% -> 63 (Python's round() gives 62).
    fifteen = {"awareness": 1, "cash_flow": 2, "pricing": 1, "debt": 3,
               "reserves": 0, "growth": 3, "mindset": 3, "compliance": 2}
    assert ff.financial_health_pct(fifteen) == 63
    assert ff.financial_health_pct({**fifteen, "reserves": 0, "growth": 0, "mindset": 0, "debt": 0}) == 25  # 6/24


def test_framework_is_complete():
    assert len(ff.FINANCE_CATEGORIES) == 8
    for c in ff.FINANCE_CATEGORIES:
        assert c["anchor"].endswith("?")
        assert len(c["followups"]) == 2
        assert set(c["rubric"]) == set(c["recommendations"]) == {0, 1, 2, 3}
        text = " ".join([c["name"], c["anchor"], *c["followups"], *c["rubric"].values(), *c["recommendations"].values()])
        assert "—" not in text and "$" not in text and "dollar" not in text.lower()
    assert ff.recommendation_for("pricing", 0) == "Run a cost-per-unit exercise immediately"


def test_progress_shows_money_habits_between_scan_and_deeper_questions():
    state, _ = _at_money_habits()
    progress = cb.session_progress(state)
    assert progress["label"] == "Money habits"
    assert (progress["finance_done"], progress["finance_total"]) == (0, 8)
    assert "finance_score" not in str(progress)


def test_anchor_prompt_spells_out_followup_rule_and_rwandan_francs():
    state, target = _at_money_habits()
    prompt = cb.build_system_prompt(state, current_target=target, next_target_after=None, is_first_turn=False)
    assert "is 0 or 1, do NOT ask the next question" in prompt
    assert "Rwandan francs" in prompt
    for q in ff.FINANCE_MAP["awareness"]["followups"]:
        assert q in prompt


def test_old_in_progress_session_without_finance_keys_enters_money_habits():
    state, _ = _at_money_habits()
    for key in ("finance", "finance_idx", "finance_phase", "finance_followups"):
        state.pop(key)
    state["stage"] = "scan"  # still answering Scan when the deploy landed
    target = cb.next_target(state)
    assert target["stage"] == "finance" and target["category"]["key"] == "awareness"


# ───────────────────── report data ─────────────────────

def _completed_state():
    state, target = _at_money_habits()
    _run_money_habits(state, target)
    return state


def test_report_receives_finance_scores_and_health_pct(monkeypatch):
    state = _completed_state()
    pack = rg._build_evidence_pack(state, [])
    assert "=== MONEY HABITS" in pack
    assert "Financial health: 71%" in pack
    assert "debt follow-up answer" in pack

    report, sid = _generate(monkeypatch, state, {})
    scores = report.scores_json
    assert scores["financial_health_pct"] == 71
    assert scores["finance_followups"] == ["awareness", "debt", "growth"]
    assert scores["finance"]["debt"] == {
        "name": "Debt and Financing", "score": 1, "unclear": False,
        "followed_up": True, "rationale": "PRIVATE debt",
    }

    client_view = dash._report_payload(report, session_id=sid)
    advisor_view = dash._report_payload(report, session_id=sid, include_rationales=True)
    assert client_view["financial_health_pct"] == 71
    assert all("rationale" not in v for v in client_view["finance_results"].values()), "leak"
    assert advisor_view["finance_results"]["debt"]["rationale"] == "PRIVATE debt"


def test_old_session_without_finance_data_still_generates_report(monkeypatch):
    state = _completed_state()
    for key in ("finance", "finance_idx", "finance_phase", "finance_followups"):
        state.pop(key)
    assert "(not covered in this interview)" in rg._build_evidence_pack(state, [])

    report, sid = _generate(monkeypatch, state, {})
    assert report.scores_json["finance"] == {}
    assert report.scores_json["financial_health_pct"] is None
    payload = dash._report_payload(report, session_id=sid)
    assert payload["finance_results"] == {} and payload["financial_health_pct"] is None
    assert sorted(payload["scan_results"]) == cb.SCAN_AREA_KEYS
