"""Scan, Branch, Triangulate diagnostic chatbot.

A deterministic state machine drives the interview. Each turn:
  1. The user's message is saved as a chat_message.
  2. The state machine determines the current and next target.
  3. Claude is asked to (a) extract a structured answer from the user's last
     message via the record_answer tool, and (b) phrase the next question
     naturally for the client.
  4. The state is mutated based on the extraction, the assistant text is saved
     and returned, and the session is marked complete when all stages are done.

The chatbot never tells the client their scores or any internal diagnosis.
"""
from __future__ import annotations

import json
import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.chat_message import ChatMessage, MessageRole
from app.models.diagnostic_session import DiagnosticSession, SessionStatus

log = logging.getLogger("musper.chatbot")


# ───────────────────── methodology constants ─────────────────────

SNAPSHOT_STEPS: list[dict[str, Any]] = [
    {"id": "company_name", "topic": "the name of the company they are calling about",
     "extracts": ["company_name"]},
    {"id": "sector", "topic": "the sector or industry the business operates in",
     "extracts": ["sector"]},
    {"id": "years_in_operation", "topic": "how many years the business has been operating",
     "extracts": ["years_in_operation"]},
    {"id": "team_size", "topic": "roughly how many people work in the business today",
     "extracts": ["team_size"]},
    {"id": "revenue_range", "topic": "their approximate annual revenue or annual budget range",
     "extracts": ["revenue_range"]},
    {"id": "person_identity", "topic": "the user's own name and their role in the business",
     "extracts": ["person_name", "person_role"]},
]

# Areas in the Scan stage. Each has two parts:
#   - audience_topic: what the question is about, in audience-facing language.
#     This is the only thing the user should ever hear.
#   - model_guidance: a private note about what you are listening for. Used in
#     the system prompt to shape scoring; must never be repeated to the user.
SCAN_AREAS: list[dict[str, Any]] = [
    {
        "key": "A",
        "name": "Strategic Clarity",
        "audience_topic": (
            "where they want the business to be in two to three years, "
            "and how clear the plan is for getting there"
        ),
        "model_guidance": (
            "You are listening for whether they have a real, owned strategic "
            "direction or whether the business is operating reactively."
        ),
    },
    {
        "key": "B",
        "name": "Operations and Systems",
        "audience_topic": (
            "how the business runs day to day, and whether important processes "
            "are written down or live mostly in people's heads"
        ),
        "model_guidance": (
            "You are gauging operational maturity. Key signals: documentation, "
            "single-person dependencies, and how repeatable delivery is."
        ),
    },
    {
        "key": "C",
        "name": "People and Capacity",
        "audience_topic": (
            "how the team is set up today, and whether they have the right "
            "people and skills to deliver what the business is trying to do"
        ),
        "model_guidance": (
            "Listen for headcount adequacy, skill gaps, and any retention "
            "or motivation issues."
        ),
    },
    {
        "key": "D",
        "name": "Funding and Resource Mobilization",
        "audience_topic": (
            "how the business is funded, how predictable that money is, "
            "and whether it matches what they are trying to deliver"
        ),
        "model_guidance": (
            "Listen for funding diversity, cash predictability, and whether "
            "resources match ambitions."
        ),
    },
    {
        "key": "E",
        "name": "Governance and Structure",
        "audience_topic": (
            "how big decisions get made in the business, and whether there is "
            "a board, advisors, or other governance helping move things"
        ),
        "model_guidance": (
            "Listen for whether governance exists on paper only, whether "
            "decisions get stuck, and who is empowered to call the shots."
        ),
    },
    {
        "key": "F",
        "name": "Stakeholder and Customer Engagement",
        "audience_topic": (
            "how the business brings customers or beneficiaries in, and how "
            "well it keeps them engaged once they are in"
        ),
        "model_guidance": (
            "Listen for whether the bigger weakness is acquisition or retention."
        ),
    },
]

SCAN_AREA_KEYS: list[str] = [a["key"] for a in SCAN_AREAS]
SCAN_AREA_MAP: dict[str, dict[str, Any]] = {a["key"]: a for a in SCAN_AREAS}

# Branch questions. Each fires only when the matching Scan area scored 1–3.
# Phrased as one conversational turn that may cover multiple sub-points;
# the model handles internal conditional logic gracefully.
BRANCH_QUESTIONS: dict[str, str] = {
    "A": (
        "Ask whether there is a written strategy or business plan today. "
        "If yes but it isn't being followed, ask what stops it being followed "
        "(resources, buy-in, unclear ownership, or that it no longer matches "
        "reality). Also ask when it was last revisited and what has changed "
        "since. You can ask all of this in one warm turn."
    ),
    "B": (
        "Ask them to walk you through how one core process (a sale, a client "
        "request, a membership renewal, whichever fits their business) "
        "actually happens today, step by step. Then ask where it breaks down "
        "or slows most, and whether it is a tools problem, a people problem, "
        "or a decision-rights problem."
    ),
    "C": (
        "Ask whether the gap is a skills gap, a headcount gap, or a "
        "motivation/retention gap. If they say skills, ask which specific "
        "skill is missing and what the gap is costing them. Also ask whether "
        "leaders have had any formal training in the last two years."
    ),
    "D": (
        "Ask whether they have applied for funding and been rejected, or have "
        "not applied at all. If rejected, ask the reason given. If not "
        "applied, ask what's stopping them — no funder pipeline, no capacity "
        "to write proposals, or no track record they can point to."
    ),
    "E": (
        "Ask whether a board or governance structure exists on paper but "
        "doesn't really function, or doesn't exist at all. Then ask what "
        "specific decisions are currently stuck waiting on governance."
    ),
    "F": (
        "Ask whether the bigger issue is acquisition (bringing customers in) "
        "or retention (keeping them). If retention, ask at what point in the "
        "relationship customers tend to disengage."
    ),
}

TRIANGULATE_STEPS: list[dict[str, str]] = [
    {
        "id": "magic_wand",
        "topic": (
            "If the biggest issue they've described disappeared tomorrow, "
            "what would actually change for the business? You are looking for "
            "what they think the unlock would be."
        ),
    },
    {
        "id": "already_tried",
        "topic": (
            "What they have already tried to fix this, and why it did not "
            "work. Be curious, not accusatory."
        ),
    },
    {
        "id": "ownership",
        "topic": (
            "Whose problem this is inside the organization — who feels it "
            "most, and who actually has the power to fix it."
        ),
    },
    {
        "id": "single_fix",
        "topic": (
            "If they could fix ONE thing in the next six months, what would "
            "it be."
        ),
    },
    {
        "id": "budget_appetite",
        "topic": (
            "Their budget and timeline appetite: roughly are they looking for "
            "a quick consult, or a six to twelve month engagement. It's fine "
            "for them to give a range."
        ),
    },
]
TRIANGULATE_KEYS: list[str] = [t["id"] for t in TRIANGULATE_STEPS]


# ───────────────────── state shape & state machine ─────────────────────

def init_state() -> dict[str, Any]:
    return {
        "stage": "snapshot",
        "snapshot_step_idx": 0,
        "snapshot": {
            "company_name": None,
            "sector": None,
            "years_in_operation": None,
            "team_size": None,
            "revenue_range": None,
            "person_name": None,
            "person_role": None,
        },
        # Tracks Snapshot fields where we've already burned the one allowed
        # "you typed nothing parseable" follow-up, so we never loop forever.
        "snapshot_clarified": {step["id"]: False for step in SNAPSHOT_STEPS},
        "scan_area_idx": 0,
        "scan": {
            k: {"score": None, "answer": None, "rationale": None, "clarified": False}
            for k in SCAN_AREA_KEYS
        },
        "branch_order": [],
        "branch_idx": 0,
        "branch": {k: None for k in SCAN_AREA_KEYS},
        "triangulate_idx": 0,
        "triangulate": {k: None for k in TRIANGULATE_KEYS},
        "current_target": None,
    }


def next_target(state: dict[str, Any]) -> dict[str, Any] | None:
    """Determine which question to ask next. Mutates `stage` when it crosses
    a boundary (e.g. all Snapshot done -> stage becomes 'scan')."""
    # Snapshot
    if state["stage"] == "snapshot":
        if state["snapshot_step_idx"] < len(SNAPSHOT_STEPS):
            step = SNAPSHOT_STEPS[state["snapshot_step_idx"]]
            return {"stage": "snapshot", "step": step}
        state["stage"] = "scan"

    # Scan
    if state["stage"] == "scan":
        if state["scan_area_idx"] < len(SCAN_AREAS):
            area = SCAN_AREAS[state["scan_area_idx"]]
            return {"stage": "scan", "area": area}
        # Compute branch_order: only areas with score 1–3, in original order
        state["branch_order"] = [
            k for k in SCAN_AREA_KEYS
            if state["scan"][k]["score"] is not None and state["scan"][k]["score"] <= 3
        ]
        state["branch_idx"] = 0
        state["stage"] = "branch"

    # Branch
    if state["stage"] == "branch":
        if state["branch_idx"] < len(state["branch_order"]):
            area_key = state["branch_order"][state["branch_idx"]]
            return {
                "stage": "branch",
                "area": SCAN_AREA_MAP[area_key],
                "question_topic": BRANCH_QUESTIONS[area_key],
            }
        state["stage"] = "triangulate"

    # Triangulate
    if state["stage"] == "triangulate":
        if state["triangulate_idx"] < len(TRIANGULATE_STEPS):
            step = TRIANGULATE_STEPS[state["triangulate_idx"]]
            return {"stage": "triangulate", "step": step}
        state["stage"] = "complete"

    return None  # interview complete


def _has_real_content(value: str | None) -> bool:
    """A loose check for genuinely empty / single-character / gibberish answers."""
    if not value:
        return False
    cleaned = value.strip()
    return len(cleaned) >= 2


def apply_extraction(
    state: dict[str, Any], target: dict[str, Any], extraction: dict[str, Any]
) -> bool:
    """Apply the model's extraction to state. Returns True if we should advance
    to the next target. Returns False when we are deliberately staying on the
    same question to ask a clarifying follow-up.

    Stage-aware rule:
      - SNAPSHOT: accept the answer directly. The only exception is when the
        model reports needs_clarification AND the user's reply is empty or a
        single character; in that case we allow one (and only one) follow-up
        per Snapshot step, then force-advance.
      - SCAN: the model may clarify once per area. After that, default to 3
        and move on (handled below).
      - BRANCH / TRIANGULATE: free-form recall; we never re-ask. Whatever the
        user said is what we record.
    """
    extraction = extraction or {}
    raw_status = extraction.get("status")
    extracted_value = (extraction.get("extracted_value") or "").strip()
    stage = target["stage"]

    if raw_status == "needs_clarification":
        if stage == "snapshot":
            step_id = target["step"]["id"]
            already_clarified = state.get("snapshot_clarified", {}).get(step_id, False)
            if not already_clarified and not _has_real_content(extracted_value):
                # First time the model has flagged this Snapshot step AND the
                # reply really was empty - allow one clarifying follow-up.
                state.setdefault("snapshot_clarified", {})[step_id] = True
                return False
            # Otherwise: force-advance, ignoring the clarification request.
            # The model was overzealous; Snapshot answers are facts.
        elif stage == "scan":
            area_key = target["area"]["key"]
            if not state["scan"][area_key]["clarified"]:
                state["scan"][area_key]["clarified"] = True
                return False
            # Already clarified once. Fall through and force-advance (score
            # will default to 3 below since the extraction has no score).
        # Branch / Triangulate: clarification not allowed in this stage - fall
        # through to the "answered" path.

    elif raw_status not in (None, "answered"):
        log.warning("Unexpected extraction status %r; treating as 'answered'.", raw_status)

    if target["stage"] == "snapshot":
        snap = (extraction or {}).get("snapshot") or {}
        # The model may also drop the bare extracted_value when only one field
        # is targeted; honour that as a fallback.
        if not snap and len(target["step"]["extracts"]) == 1:
            snap = {target["step"]["extracts"][0]: extracted_value}
        for key in target["step"]["extracts"]:
            value = snap.get(key)
            if value is not None and value != "":
                state["snapshot"][key] = str(value).strip()
        state["snapshot_step_idx"] += 1

    elif target["stage"] == "scan":
        key = target["area"]["key"]
        score = (extraction or {}).get("score")
        # If the model has been clarified once and still didn't return a score,
        # default to 3 to keep the interview moving.
        if score is None and state["scan"][key]["clarified"]:
            score = 3
        if score is not None:
            score = max(1, min(5, int(score)))
        state["scan"][key]["score"] = score
        state["scan"][key]["answer"] = extracted_value
        state["scan"][key]["rationale"] = (extraction or {}).get("score_rationale")
        state["scan_area_idx"] += 1

    elif target["stage"] == "branch":
        state["branch"][target["area"]["key"]] = extracted_value
        state["branch_idx"] += 1

    elif target["stage"] == "triangulate":
        state["triangulate"][target["step"]["id"]] = extracted_value
        state["triangulate_idx"] += 1

    return True


# ───────────────────── prompt construction ─────────────────────

VOICE_GUIDE = """\
VOICE:
- You sound like a calm Rwandan business consultant having a coffee conversation
  with the client. Warm, practical, never robotic.
- Vary your acknowledgments. Avoid repeating "Thank you for sharing" or "That makes sense"
  every turn. Sometimes just go straight to the next question.
- Never use em-dashes. Use commas, periods, or restructure the sentence.
- No filler phrases like "in today's fast-paced world", "absolutely", "I appreciate your transparency".
- Short, plain sentences. Avoid consulting jargon (no "stakeholder ecosystems", "value chains").
- ONE question per turn. Never ask multi-part questions joined by "and also".
- Never tell the client their score or your diagnosis. You only collect.
- Stay strictly on the diagnostic. If they ask unrelated things, politely redirect.
"""

CLARIFICATION_RULES = """\
CLARIFICATION RULES (very important, varies per stage):

- SNAPSHOT stage: these are simple facts (company name, sector, years operating,
  team size, revenue range, the user's name and role). ACCEPT WHATEVER THE
  USER SAYS, even if it is brief. Do not probe. Do not ask "could you tell me
  more". Do not ask for elaboration. status='answered' every time.
  The ONLY exception: if the reply is literally empty or pure gibberish such
  as "asdfgh" or a single character, then status='needs_clarification' is
  allowed once.

- SCAN stage: this is where you privately score the answer 1 to 5. If the
  user's answer is too vague to confidently infer a score AND you have not
  already used a clarification for this area, you may set
  status='needs_clarification' ONCE per area. Otherwise status='answered'.

- BRANCH stage: record whatever the user said. Do not probe further; the
  consultant can pick that up in person. status='answered' every time.

- TRIANGULATE stage: same as Branch. Record their reflection as given.
  status='answered' every time.
"""

METHODOLOGY = """\
THE INTERVIEW METHOD: Scan, Branch, Triangulate

You guide the client through four stages, in this exact order:

1. SNAPSHOT - collect six basic facts about the business, one question at a time,
   conversationally. Never ask all at once.

2. SCAN - one diagnostic question about each of six areas (A-F). You phrase a real
   question that lets the client describe their reality, then you privately infer
   a score from 1 (critical gap) to 5 (strong). You never say the score out loud.

3. BRANCH - only for areas that scored 1-3, you ask the matching deeper question.
   Areas scored 4-5 are skipped entirely.

4. TRIANGULATE - five reflective questions every client gets, regardless of scores.

The backend (not you) tracks which stage you are in and which question is next.
Each turn, you will be told exactly what question to ask next.
"""

RECORD_TOOL: dict[str, Any] = {
    "name": "record_answer",
    "description": (
        "Record what the user just said in structured form, so the backend can "
        "update its state. You MUST call this tool every turn except the very "
        "first message of the interview."
    ),
    "input_schema": {
        "type": "object",
        "required": ["status"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["answered", "needs_clarification"],
                "description": (
                    "'answered' when the user has given you enough to record an "
                    "answer for the question you most recently asked. "
                    "'needs_clarification' when their reply was so vague or "
                    "off-topic that you cannot confidently extract anything; "
                    "use this sparingly (at most once per area)."
                ),
            },
            "extracted_value": {
                "type": "string",
                "description": (
                    "A concise textual record of the user's substantive answer "
                    "to the question you most recently asked. For Snapshot fields, "
                    "this is the bare fact. For Scan/Branch/Triangulate, summarize "
                    "their answer in 1-3 sentences. Leave empty if status is "
                    "'needs_clarification'."
                ),
            },
            "score": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": (
                    "ONLY when answering a Scan question and status='answered': "
                    "the score (1=critical gap, 2=weak, 3=mid, 4=good, 5=strong) "
                    "you privately infer for that area from this answer."
                ),
            },
            "score_rationale": {
                "type": "string",
                "description": (
                    "ONLY for Scan: 1-2 short sentences explaining why this score, "
                    "for internal use later by the advisor. Never spoken to the user."
                ),
            },
            "snapshot": {
                "type": "object",
                "description": (
                    "ONLY when answering a Snapshot question and status='answered'. "
                    "An object with the field(s) the user provided. Keys are: "
                    "company_name, sector, years_in_operation, team_size, "
                    "revenue_range, person_name, person_role."
                ),
                "properties": {
                    "company_name": {"type": "string"},
                    "sector": {"type": "string"},
                    "years_in_operation": {"type": "string"},
                    "team_size": {"type": "string"},
                    "revenue_range": {"type": "string"},
                    "person_name": {"type": "string"},
                    "person_role": {"type": "string"},
                },
            },
        },
    },
}


def _describe_target(target: dict[str, Any] | None) -> str:
    """Builds the per-target instruction for the model. Note: audience_topic /
    topic strings are pure subject matter (safe if echoed back to the user);
    model_guidance / question_topic strings are private notes for the model
    and must be clearly marked as such so they don't leak into output."""
    if target is None:
        return "(none - interview is finishing)"
    stage = target["stage"]
    if stage == "snapshot":
        return (
            f"Snapshot step '{target['step']['id']}': ask one short, direct "
            f"question about {target['step']['topic']}. Phrase it naturally, "
            "as a one-line question."
        )
    if stage == "scan":
        a = target["area"]
        return (
            f"Scan area {a['key']} ({a['name']}). Ask the client ONE natural, "
            f"open question about {a['audience_topic']}. "
            f"[Private listening guidance, do NOT repeat in your text reply: "
            f"{a['model_guidance']}]"
        )
    if stage == "branch":
        a = target["area"]
        return (
            f"Branch question for area {a['key']} ({a['name']}). [Private guidance, "
            f"do NOT quote verbatim, rephrase naturally as one warm turn: "
            f"{target['question_topic']}]"
        )
    if stage == "triangulate":
        return (
            f"Triangulate question '{target['step']['id']}'. Ask the client about "
            f"{target['step']['topic']}"
        )
    return "(unknown)"


def _state_summary_lines(state: dict[str, Any]) -> str:
    snap = state["snapshot"]
    lines: list[str] = [f"  Stage: {state['stage']}"]
    company = snap.get("company_name") or "?"
    person = snap.get("person_name") or "?"
    lines.append(f"  Company so far: {company}; speaking to: {person}")
    scan_summary = []
    for k in SCAN_AREA_KEYS:
        s = state["scan"][k]["score"]
        scan_summary.append(f"{k}:{s if s is not None else '-'}")
    lines.append(f"  Scan scores so far (private): {' '.join(scan_summary)}")
    if state["stage"] in ("branch", "triangulate"):
        lines.append(f"  Branch areas to cover: {state['branch_order'] or 'none'}")
    return "\n".join(lines)


def build_system_prompt(
    state: dict[str, Any],
    current_target: dict[str, Any] | None,
    next_target_after: dict[str, Any] | None,
    *,
    is_first_turn: bool,
) -> str:
    parts: list[str] = []
    parts.append(
        "You are the diagnostic interviewer for Musper Solutions, a business "
        "consultancy based in Kigali, Rwanda. Your job is to run a structured "
        "fifteen to twenty minute interview that captures how the client's "
        "business is really doing."
    )
    parts.append(VOICE_GUIDE)
    parts.append(METHODOLOGY)
    parts.append(CLARIFICATION_RULES)
    parts.append("CURRENT INTERVIEW STATE (private, never reveal):\n" + _state_summary_lines(state))
    if is_first_turn:
        parts.append(
            "THIS TURN:\n"
            "- This is your very first message of the interview.\n"
            "- Briefly introduce yourself and what the interview is for "
            "(a guided business diagnostic on behalf of Musper Solutions), "
            "in two or three short sentences.\n"
            f"- Then ask the first question: {_describe_target(next_target_after)}\n"
            "- Do NOT call the record_answer tool on this turn — there's no "
            "user answer to record yet."
        )
    else:
        current_stage = (current_target or {}).get("stage")
        parts.append(
            "THIS TURN:\n"
            f"- The question you just asked was: {_describe_target(current_target)}\n"
            f"- You are in the {current_stage.upper() if current_stage else 'UNKNOWN'} stage. "
            "Re-read the CLARIFICATION RULES above and apply them.\n"
            "- First, call the record_answer tool exactly once to record what the user "
            "just said. Pick status based on the stage rules above. For Snapshot, that "
            "almost always means status='answered'."
        )
        if next_target_after is None:
            parts.append(
                "- Then write a warm one or two sentence closing thanking them and "
                "telling them that Penny will personally review the responses and "
                "follow up. Do not share any results or assessments."
            )
        else:
            parts.append(
                "- Then write the message the user will see. If status='answered', "
                "give a brief one-line acknowledgment (vary the phrasing across turns, "
                "sometimes skip it entirely) and ask the next question.\n"
                f"- The next question to ask: {_describe_target(next_target_after)}\n"
                "- If, and only if, you set status='needs_clarification', ask a single "
                "short follow-up about the SAME question you just asked, not the next "
                "one."
            )
    parts.append(
        "OUTPUT FORMAT (strict):\n"
        "1. Your reply MUST contain a record_answer tool call AND a natural-language "
        "text message. The text is what the client sees.\n"
        "2. The text message MUST end with the actual next question phrased as a "
        "question (ending in '?'). 'Good.' or 'Got it.' alone is NOT acceptable; "
        "always include the next question right after.\n"
        "3. NEVER echo or quote the private 'Listening guidance' or 'guidance' "
        "snippets from these instructions into your text reply. The client must "
        "not see internal notes.\n"
        "4. Never reveal scores or your internal reasoning to the client."
    )
    return "\n\n".join(parts)


_PRIVATE_LEAK_MARKERS = (
    "Private listening guidance",
    "Private guidance",
    "You are listening for",
    "You are gauging",
    "Listen for whether",
    "Listen for",
    "do NOT repeat",
    "do NOT quote",
)


def _strip_leaked_guidance(text: str) -> str:
    """Defensive: if the model echoed the private listening guidance into its
    reply, trim it. We do this by truncating at the first marker line."""
    if not text:
        return text
    for marker in _PRIVATE_LEAK_MARKERS:
        idx = text.find(marker)
        if idx > 0:
            # Cut back to the previous sentence end or paragraph break.
            head = text[:idx]
            # Trim a trailing partial sentence opener like "[" or "("
            head = head.rstrip().rstrip("[(")
            return head.rstrip()
    return text


def _fallback_next_question(target: dict[str, Any] | None) -> str:
    """Used when Claude returns a valid tool call but no text. We synthesise the
    next question deterministically so the user never sees a 'tell me more'
    pseudo-clarification when the answer was accepted."""
    if target is None:
        return (
            "Thanks for going through all of that. Your responses are saved. "
            "Penny will personally review them and follow up with you."
        )
    stage = target["stage"]
    if stage == "snapshot":
        return {
            "company_name": "To start, what is the name of the business?",
            "sector": "What sector or industry is the business in?",
            "years_in_operation": "How long has the business been operating?",
            "team_size": "Roughly how many people work in the business today?",
            "revenue_range": "What is your approximate annual revenue or annual budget range?",
            "person_identity": "Last bit of context. What is your name, and what is your role in the business?",
        }.get(
            target["step"]["id"],
            "Could you share a little more about the business so we can move on?",
        )
    if stage == "scan":
        area = target["area"]
        return f"Now, can you tell me about {area['audience_topic']}?"
    if stage == "branch":
        return (
            "Staying on that area for a moment: " + target["question_topic"]
        )
    if stage == "triangulate":
        return "A reflective question. " + target["step"]["topic"]
    return "Please continue."


# ───────────────────── Anthropic plumbing ─────────────────────

_anthropic_client = None


def _get_client():
    global _anthropic_client
    if _anthropic_client is None:
        if not settings.anthropic_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "Diagnostic chatbot unavailable: the ANTHROPIC_API_KEY "
                    "environment variable is not set on the backend."
                ),
            )
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Anthropic SDK is not installed on the backend.",
            ) from exc
        _anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    return _anthropic_client


def _call_claude(
    *, system_prompt: str, history: list[dict[str, str]]
) -> tuple[str, dict[str, Any] | None]:
    """One round trip. Returns (assistant_text, extraction_dict_or_None)."""
    client = _get_client()
    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            system=system_prompt,
            tools=[RECORD_TOOL],
            messages=history,
        )
    except Exception as exc:
        log.exception("Anthropic call failed.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Diagnostic service upstream error: {exc}",
        ) from exc

    text_chunks: list[str] = []
    extraction: dict[str, Any] | None = None
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            text_chunks.append(block.text)
        elif block_type == "tool_use" and block.name == "record_answer":
            try:
                extraction = dict(block.input)
            except Exception:
                extraction = json.loads(block.input)  # type: ignore[arg-type]

    text = "\n".join(c.strip() for c in text_chunks if c and c.strip())
    return text, extraction


# ───────────────────── public service entry points ─────────────────────

def start_session(db: Session, *, client_id) -> tuple[DiagnosticSession, ChatMessage]:
    """Create a new diagnostic session and emit the first assistant message."""
    state = init_state()
    target = next_target(state)  # first snapshot question

    system_prompt = build_system_prompt(
        state,
        current_target=None,
        next_target_after=target,
        is_first_turn=True,
    )
    history = [
        {"role": "user", "content": "[Begin the interview.]"},
    ]
    assistant_text, _ = _call_claude(system_prompt=system_prompt, history=history)
    if not assistant_text:
        assistant_text = (
            "Hi, I'm Musper's diagnostic interviewer. I'll ask a few questions "
            "to get a clear picture of where your business is right now. "
            "To start, what's the name of the business you're calling about?"
        )

    state["current_target"] = target
    session = DiagnosticSession(
        client_id=client_id,
        status=SessionStatus.in_progress,
        diagnostic_state=state,
    )
    db.add(session)
    db.flush()
    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.assistant,
        content=assistant_text,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(session)
    db.refresh(assistant_msg)
    return session, assistant_msg


def submit_user_message(
    db: Session, *, session: DiagnosticSession, content: str
) -> tuple[ChatMessage, ChatMessage, bool]:
    """Record the user's message and produce the next assistant message.

    Returns (saved_user_msg, saved_assistant_msg, is_complete).
    """
    if session.status == SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This diagnostic session has already been completed.",
        )

    state: dict[str, Any] = deepcopy(session.diagnostic_state or init_state())
    current_target = state.get("current_target")

    # Persist the user's message
    user_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.user,
        content=content.strip(),
    )
    db.add(user_msg)
    db.flush()

    # Build the model history out of the actual transcript
    db.refresh(session)
    transcript = list(session.messages)
    transcript.sort(key=lambda m: m.created_at)
    history = [
        {
            "role": "assistant" if m.role == MessageRole.assistant else "user",
            "content": m.content,
        }
        for m in transcript
    ]

    # First, peek the *next* target as if extraction succeeds (used to phrase
    # the upcoming question in this turn's response). We do this BEFORE applying
    # the extraction by working on a shadow state.
    shadow = deepcopy(state)
    shadow_current = current_target
    # Simulate "this turn's extraction succeeded" by virtually advancing.
    # (Used purely for prompting; real state is mutated post-extraction.)
    if shadow_current is not None:
        # We don't have the real extraction yet; assume it will be 'answered' for
        # the purpose of describing the NEXT question.
        if shadow_current["stage"] == "snapshot":
            shadow["snapshot_step_idx"] += 1
        elif shadow_current["stage"] == "scan":
            shadow["scan_area_idx"] += 1
        elif shadow_current["stage"] == "branch":
            shadow["branch_idx"] += 1
        elif shadow_current["stage"] == "triangulate":
            shadow["triangulate_idx"] += 1
    next_after = next_target(shadow)

    system_prompt = build_system_prompt(
        state,
        current_target=current_target,
        next_target_after=next_after,
        is_first_turn=False,
    )
    assistant_text, extraction = _call_claude(system_prompt=system_prompt, history=history)

    # Mutate the real state based on the actual extraction
    if current_target is not None:
        apply_extraction(state, current_target, extraction or {"status": "answered"})

    # Recompute next target for real
    real_next = next_target(state)
    is_complete = real_next is None
    state["current_target"] = real_next

    # Defensive cleanup: trim any leaked private guidance the model may have
    # echoed from the system prompt.
    assistant_text = _strip_leaked_guidance(assistant_text)

    if not assistant_text:
        # The model gave us a tool call but no text. Don't beg for clarification:
        # synthesise the next question deterministically so the conversation flows.
        assistant_text = _fallback_next_question(real_next)
    elif real_next is not None and "?" not in assistant_text:
        # Model gave a terse acknowledgment without an actual question. Append
        # the deterministic next question so the user always knows what to answer.
        assistant_text = f"{assistant_text.rstrip().rstrip('.')}. {_fallback_next_question(real_next)}"

    assistant_msg = ChatMessage(
        session_id=session.id,
        role=MessageRole.assistant,
        content=assistant_text,
    )
    db.add(assistant_msg)
    session.diagnostic_state = state
    if is_complete:
        session.status = SessionStatus.completed
        session.completed_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    db.refresh(user_msg)
    db.refresh(assistant_msg)
    return user_msg, assistant_msg, is_complete


def session_progress(state: dict[str, Any] | None) -> dict[str, Any]:
    """Public progress summary - safe to send to the client UI. No scores."""
    if not state:
        return {"stage": "not_started", "label": "Not started", "completed_steps": 0, "total_steps": 0}
    stage = state.get("stage", "snapshot")
    labels = {
        "snapshot": "Snapshot",
        "scan": "Scan",
        "branch": "Deeper questions",
        "triangulate": "Final reflections",
        "complete": "Complete",
    }
    return {
        "stage": stage,
        "label": labels.get(stage, stage),
        "snapshot_done": state.get("snapshot_step_idx", 0),
        "snapshot_total": len(SNAPSHOT_STEPS),
        "scan_done": state.get("scan_area_idx", 0),
        "scan_total": len(SCAN_AREAS),
        "branch_done": state.get("branch_idx", 0),
        "branch_total": len(state.get("branch_order", [])),
        "triangulate_done": state.get("triangulate_idx", 0),
        "triangulate_total": len(TRIANGULATE_STEPS),
    }
