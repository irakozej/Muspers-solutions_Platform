"""Unit tests for the diagnostic state machine. No Claude calls."""
from app.services import diagnostic_chatbot as cb


def _advance(state, target, extraction):
    """Apply extraction + recompute next target, mirroring the runtime loop."""
    cb.apply_extraction(state, target, extraction)
    return cb.next_target(state)


def _strong_money_habits(state, target):
    """Answer all eight Money Habits anchors strongly (no follow-ups)."""
    for _ in range(len(cb.FINANCE_CATEGORIES)):
        assert target["stage"] == "finance"
        target = _advance(state, target, {"status": "answered", "extracted_value": "...", "finance_score": 3})
    return target


def test_initial_target_is_first_snapshot_step():
    state = cb.init_state()
    target = cb.next_target(state)
    assert target is not None
    assert target["stage"] == "snapshot"
    assert target["step"]["id"] == "company_name"


def test_snapshot_advances_field_by_field_then_enters_scan():
    state = cb.init_state()
    snapshot_answers = [
        {"status": "answered", "snapshot": {"company_name": "Inyange Foods"}},
        {"status": "answered", "snapshot": {"sector": "Agro-processing"}},
        {"status": "answered", "snapshot": {"years_in_operation": "11"}},
        {"status": "answered", "snapshot": {"team_size": "45"}},
        {"status": "answered", "snapshot": {"revenue_range": "200M-500M RWF"}},
        {"status": "answered", "snapshot": {"person_name": "Marie", "person_role": "CEO"}},
    ]
    target = cb.next_target(state)
    for extraction in snapshot_answers:
        target = _advance(state, target, extraction)
    # After all 6 snapshot steps, we should be in Scan, area A
    assert state["stage"] == "scan"
    assert target["stage"] == "scan"
    assert target["area"]["key"] == "A"
    assert state["snapshot"]["company_name"] == "Inyange Foods"
    assert state["snapshot"]["person_name"] == "Marie"
    assert state["snapshot"]["person_role"] == "CEO"


def test_full_scan_records_six_scores_in_order():
    state = cb.init_state()
    # Skip past snapshot programmatically
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    target = cb.next_target(state)
    scores = {"A": 5, "B": 4, "C": 2, "D": 1, "E": 4, "F": 3}
    for k in ["A", "B", "C", "D", "E", "F"]:
        assert target["stage"] == "scan"
        assert target["area"]["key"] == k
        target = _advance(
            state,
            target,
            {"status": "answered", "extracted_value": f"answer for {k}", "score": scores[k]},
        )
    # After Scan comes Money Habits, then Branch with the correct branch_order (only 1-3)
    assert state["stage"] == "finance"
    _strong_money_habits(state, target)
    assert state["stage"] == "branch"
    assert state["branch_order"] == ["C", "D", "F"]


def test_branch_only_runs_for_weak_areas_then_triangulate():
    state = cb.init_state()
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    scores = {"A": 5, "B": 4, "C": 2, "D": 1, "E": 4, "F": 3}
    target = cb.next_target(state)
    for k in ["A", "B", "C", "D", "E", "F"]:
        target = _advance(
            state,
            target,
            {"status": "answered", "extracted_value": "...", "score": scores[k]},
        )
    target = _strong_money_habits(state, target)
    # We're now at the first branch target
    assert target["stage"] == "branch"
    assert target["area"]["key"] == "C"
    target = _advance(state, target, {"status": "answered", "extracted_value": "C branch answer"})
    assert target["stage"] == "branch"
    assert target["area"]["key"] == "D"
    target = _advance(state, target, {"status": "answered", "extracted_value": "D branch answer"})
    assert target["stage"] == "branch"
    assert target["area"]["key"] == "F"
    target = _advance(state, target, {"status": "answered", "extracted_value": "F branch answer"})
    # Strong areas (A, B, E) were skipped entirely
    assert state["branch"]["A"] is None
    assert state["branch"]["B"] is None
    assert state["branch"]["E"] is None
    assert state["branch"]["C"] == "C branch answer"
    assert state["branch"]["D"] == "D branch answer"
    assert state["branch"]["F"] == "F branch answer"
    # Now we're in Triangulate
    assert state["stage"] == "triangulate"
    assert target["stage"] == "triangulate"
    assert target["step"]["id"] == "magic_wand"


def test_triangulate_always_asks_all_five_then_completes():
    state = cb.init_state()
    # All scan scores are 5 (strong) - so NO branch questions fire
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    target = cb.next_target(state)
    for k in ["A", "B", "C", "D", "E", "F"]:
        target = _advance(
            state, target,
            {"status": "answered", "extracted_value": "strong", "score": 5},
        )
    target = _strong_money_habits(state, target)
    assert state["branch_order"] == []
    # We jumped straight to triangulate
    assert state["stage"] == "triangulate"
    assert target["stage"] == "triangulate"
    for key in cb.TRIANGULATE_KEYS:
        assert target["stage"] == "triangulate"
        assert target["step"]["id"] == key
        target = _advance(
            state, target,
            {"status": "answered", "extracted_value": f"answer for {key}"},
        )
    # All Triangulate done -> complete
    assert state["stage"] == "complete"
    assert target is None
    for key in cb.TRIANGULATE_KEYS:
        assert state["triangulate"][key] == f"answer for {key}"


def test_needs_clarification_does_not_advance_first_time():
    state = cb.init_state()
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    target = cb.next_target(state)  # Scan A
    # First clarification - stay on A
    advanced = cb.apply_extraction(state, target, {"status": "needs_clarification"})
    assert advanced is False
    assert state["scan"]["A"]["clarified"] is True
    target_after = cb.next_target(state)
    assert target_after["stage"] == "scan"
    assert target_after["area"]["key"] == "A"


def test_clarified_then_no_score_defaults_to_three():
    state = cb.init_state()
    state["stage"] = "scan"
    state["snapshot_step_idx"] = len(cb.SNAPSHOT_STEPS)
    target = cb.next_target(state)
    # First turn: clarify
    cb.apply_extraction(state, target, {"status": "needs_clarification"})
    # Second turn: answered but no score given
    cb.apply_extraction(state, target, {"status": "answered", "extracted_value": "vague"})
    assert state["scan"]["A"]["score"] == 3


def test_progress_label_reflects_stage():
    state = cb.init_state()
    progress = cb.session_progress(state)
    assert progress["stage"] == "snapshot"
    assert progress["label"] == "Snapshot"
    assert progress["snapshot_total"] == 6
    assert progress["scan_total"] == 6
    assert progress["triangulate_total"] == 5


# ───────────────────── stage-aware clarification tests ─────────────────────

def test_snapshot_ignores_needs_clarification_when_user_gave_real_content():
    """Snapshot answers are facts. If the model overzealously asks for
    clarification but we have a real extracted value, force-advance."""
    state = cb.init_state()
    target = cb.next_target(state)
    # Model says 'needs_clarification' but extracted a real company name anyway
    advanced = cb.apply_extraction(state, target, {
        "status": "needs_clarification",
        "extracted_value": "Inyange Foods",
        "snapshot": {"company_name": "Inyange Foods"},
    })
    assert advanced is True
    assert state["snapshot"]["company_name"] == "Inyange Foods"
    assert state["snapshot_step_idx"] == 1


def test_snapshot_honors_one_clarification_when_answer_is_truly_empty():
    """If the user types nothing parseable AND the model flags clarification,
    we allow one re-ask per Snapshot step, then force-advance."""
    state = cb.init_state()
    target = cb.next_target(state)
    # First time: gibberish input, model asks for clarification - honored.
    advanced = cb.apply_extraction(state, target, {
        "status": "needs_clarification",
        "extracted_value": "",
    })
    assert advanced is False
    assert state["snapshot_step_idx"] == 0
    assert state["snapshot_clarified"]["company_name"] is True

    # Second time on the same step: still empty, but we've already clarified.
    # The state machine force-advances rather than looping.
    advanced = cb.apply_extraction(state, target, {
        "status": "needs_clarification",
        "extracted_value": "",
    })
    assert advanced is True
    assert state["snapshot_step_idx"] == 1


def test_branch_stage_never_clarifies():
    """The user said Branch and Triangulate must never use clarification."""
    state = cb.init_state()
    # Force into the Branch stage with one weak Scan score.
    state["stage"] = "branch"
    state["branch_order"] = ["A"]
    state["branch_idx"] = 0
    state["scan"]["A"]["score"] = 2
    target = cb.next_target(state)
    assert target["stage"] == "branch"

    advanced = cb.apply_extraction(state, target, {
        "status": "needs_clarification",
        "extracted_value": "We've got a written strategy but it sits in a drawer.",
    })
    # Branch must advance even when the model says 'needs_clarification'.
    assert advanced is True
    assert state["branch"]["A"]
    assert state["branch_idx"] == 1


def test_triangulate_stage_never_clarifies():
    state = cb.init_state()
    state["stage"] = "triangulate"
    state["triangulate_idx"] = 0
    target = cb.next_target(state)
    assert target["stage"] == "triangulate"

    advanced = cb.apply_extraction(state, target, {
        "status": "needs_clarification",
        "extracted_value": "Honestly, things would just be calmer.",
    })
    assert advanced is True
    assert state["triangulate"]["magic_wand"]
    assert state["triangulate_idx"] == 1


def test_fallback_next_question_handles_all_stage_targets():
    """Regression: the fallback path must not crash on any stage's target shape.
    Previously _fallback_next_question used a stale key from SCAN_AREAS."""
    # Snapshot
    for step in cb.SNAPSHOT_STEPS:
        out = cb._fallback_next_question({"stage": "snapshot", "step": step})
        assert out and "?" in out
    # Scan - this is the case that 500'd in production
    for area in cb.SCAN_AREAS:
        out = cb._fallback_next_question({"stage": "scan", "area": area})
        assert out and "?" in out
    # Branch
    for area in cb.SCAN_AREAS:
        out = cb._fallback_next_question({
            "stage": "branch", "area": area,
            "question": cb.BRANCH_QUESTIONS[area["key"]],
        })
        assert out
    # Triangulate
    for step in cb.TRIANGULATE_STEPS:
        out = cb._fallback_next_question({"stage": "triangulate", "step": step})
        assert out
    # Complete
    out = cb._fallback_next_question(None)
    assert out
