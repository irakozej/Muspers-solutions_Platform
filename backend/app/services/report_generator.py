"""MusperSolutions' Root-Cause Diagnostic Report generator.

Takes a completed diagnostic session (structured state + full transcript),
asks Claude to do the analytical work of MusperSolutions' method, and saves the result
into the existing `reports` table so the Phase 6 dashboards and Phase 5 PDF
export keep working unchanged.

The method, in one line: the client names a symptom (the presenting problem);
the diagnostic evidence usually points to a different underlying condition
(the root cause); the service pathway treats the root cause, not the symptom.

Cost/safety notes:
- Reuses the hardened Anthropic client from diagnostic_chatbot (env-driven key,
  timeout, typed error handling, no secret or content logging).
- Output is forced through a tool schema, so the response is always parseable.
- The investment range is never model-generated. The tool schema has no field
  for it; code stamps a "to be confirmed" placeholder that MusperSolutions edits.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.scoring import band_for
from app.db.session import SessionLocal
from app.models.chat_message import MessageRole
from app.models.diagnostic_session import DiagnosticSession, SessionStatus
from app.models.report import Report
from app.services.diagnostic_chatbot import (
    SCAN_AREA_KEYS,
    SCAN_AREA_MAP,
    TRIANGULATE_KEYS,
    _BUSY_MSG,
    _RETRY_MSG,
    _get_client,
)
from app.services.finance_framework import FINANCE_CATEGORIES, FINANCE_KEYS, financial_health_pct
from app.services.report_summary import business_health_pct, priority_areas

log = logging.getLogger("musper.report")

REPORT_TYPE = "root_cause"

# Force-set in code, never model-generated (verification item 5).
INVESTMENT_PLACEHOLDER = "To be confirmed by MusperSolutions"

SERVICE_LINES: list[str] = [
    "Business Development Consulting",
    "Digital Transformation",
    "Capacity-Building and Training",
    "Coaching and Mentorship",
    "Event Management",
    "Premium Strategic Advisory",
]

ENGAGEMENT_TYPES = ["quick_consult", "project", "retainer_6_12"]
ENGAGEMENT_LABELS = {
    "quick_consult": "Quick consult",
    "project": "Defined project",
    "retainer_6_12": "6 to 12 month retainer",
}

TRIANGULATE_LABELS = {
    "magic_wand": "If the problem disappeared tomorrow",
    "already_tried": "What they already tried",
    "ownership": "Who owns the problem internally",
    "single_fix": "The one fix they would choose",
    "budget_appetite": "Budget and timeline appetite",
}


# ───────────────────── output contract ─────────────────────

REPORT_TOOL: dict[str, Any] = {
    "name": "submit_report",
    "description": (
        "Submit the finished Root-Cause Diagnostic Report as structured data. "
        "Call this exactly once, with every required field filled."
    ),
    "input_schema": {
        "type": "object",
        "required": [
            "headline",
            "scan_summaries",
            "presenting_problem",
            "root_cause",
            "root_cause_evidence",
            "already_tried",
            "ownership",
            "service_pathway",
            "engagement",
        ],
        "properties": {
            "headline": {
                "type": "string",
                "description": (
                    "One sharp sentence that captures the whole diagnosis, "
                    "naming the symptom and the underlying cause. Example shape: "
                    "'Retention looks like the problem; undocumented operations "
                    "are what is actually bleeding customers.' Plain text."
                ),
            },
            "scan_summaries": {
                "type": "object",
                "required": SCAN_AREA_KEYS,
                "properties": {
                    key: {
                        "type": "string",
                        "description": (
                            f"Area {key} ({SCAN_AREA_MAP[key]['name']}): 1-2 "
                            "sentences summarising what the client said about "
                            "this area. Draw on the whole transcript, not only "
                            "the scan answer, since clients often cover an area "
                            "in a later reply. The client will read this, so no "
                            "scores, no scoring notes, no remarks about how the "
                            "interview went. If the client never clearly "
                            "addressed the area, say that plainly."
                        ),
                    }
                    for key in SCAN_AREA_KEYS
                },
            },
            "presenting_problem": {
                "type": "string",
                "description": (
                    "2-4 sentences. What the client says the problem is, in "
                    "their own framing. Stay faithful to their words; quote a "
                    "short phrase of theirs where natural."
                ),
            },
            "root_cause": {
                "type": "string",
                "description": (
                    "3-6 sentences. What the diagnostic actually reveals is "
                    "going on underneath. This must be a genuine insight, not a "
                    "restatement of the presenting problem, and every claim must "
                    "trace back to something specific: an answer, a score, a "
                    "triangulation response. If the evidence is thin on a point, "
                    "say plainly that it is not yet clear."
                ),
            },
            "root_cause_evidence": {
                "type": "array",
                "minItems": 2,
                "maxItems": 5,
                "items": {"type": "string"},
                "description": (
                    "2-5 short evidence points, each tying the root cause to a "
                    "specific thing from the interview (a quoted phrase, a low "
                    "or high scan score, a triangulation answer)."
                ),
            },
            "already_tried": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "required": ["attempt", "why_it_failed"],
                    "properties": {
                        "attempt": {"type": "string"},
                        "why_it_failed": {
                            "type": "string",
                            "description": (
                                "Why it did not work, connected to the root "
                                "cause where the evidence supports that."
                            ),
                        },
                    },
                },
                "description": (
                    "From the 'already tried' triangulation answer plus anything "
                    "relevant in the transcript. If the client tried nothing, "
                    "one entry saying so plainly."
                ),
            },
            "ownership": {
                "type": "string",
                "description": (
                    "2-3 sentences from the ownership triangulation answer: who "
                    "feels the problem most, and who has the power to fix it."
                ),
            },
            "service_pathway": {
                "type": "array",
                "minItems": 1,
                "maxItems": 3,
                "items": {
                    "type": "object",
                    "required": ["service", "justification"],
                    "properties": {
                        "service": {"type": "string", "enum": SERVICE_LINES},
                        "justification": {
                            "type": "string",
                            "description": (
                                "1-2 sentences tying this service to the ROOT "
                                "CAUSE, not the presenting problem."
                            ),
                        },
                    },
                },
            },
            "engagement": {
                "type": "object",
                "required": ["type", "timeline", "next_step"],
                "properties": {
                    "type": {"type": "string", "enum": ENGAGEMENT_TYPES},
                    "timeline": {
                        "type": "string",
                        "description": (
                            "Estimated duration in plain words, e.g. '10 to 12 "
                            "weeks' or '6 months with monthly check-ins'."
                        ),
                    },
                    "next_step": {
                        "type": "string",
                        "description": (
                            "The concrete follow-up, e.g. 'A 45-minute scoping "
                            "call with MusperSolutions to confirm the root cause and agree "
                            "the first deliverable.'"
                        ),
                    },
                },
            },
        },
    },
}


SYSTEM_PROMPT = f"""\
You are the senior analyst behind MusperSolutions' Root-Cause Diagnostic
Report. MusperSolutions is a business consultancy in Kigali, Rwanda, founded and led by
MusperSolutions Advisory. Your job is to turn a completed diagnostic interview
into the analysis MusperSolutions will review, refine, and eventually share with the
client.

THE METHOD (MusperSolutions' philosophy, follow it exactly):
A client almost always arrives with a symptom: the thing that hurts, in the
words they use for it. That is the PRESENTING PROBLEM, and it deserves to be
recorded faithfully, in their framing. But the interview evidence, the six
scan scores, the deeper branch answers, the five triangulation responses,
usually points at a different underlying condition. That is the ROOT CAUSE.
Finding it is the entire value of this report. A root cause that merely
restates the presenting problem in consultant language is a failed report.
The service pathway then treats the root cause, never the symptom.

HOW TO REASON:
- Look for the mismatch: what the client complains about versus where the
  low scores actually sit. A client who complains about sales but scored 1
  on operations has an operations problem wearing a sales costume.
- Use the triangulation answers as the cross-check: what they already tried
  (and why it failed) usually failed BECAUSE it treated the symptom. Say so
  when the evidence supports it.
- Weigh the branch answers heavily; they were only asked where the scan
  found weakness, so they carry the most diagnostic signal.
- Always examine the Money Habits section (eight money categories scored 0
  to 3) as a candidate root cause. Weak money habits are often the condition
  underneath an operational or growth complaint: when the evidence supports
  that, connect them to the root cause explicitly. When it does not, say
  what the money habits rule in or out and do not force the link. Older
  interviews may not have this section; never invent it.
- Strong areas matter too: they rule causes out and are assets to build on.

GROUNDING RULES (non-negotiable):
- Every claim traces to something specific the client said, a score, or a
  triangulation answer. Quote short phrases of theirs where it strengthens
  the point.
- Never invent facts the interview did not surface: no imagined revenue
  figures, no assumed team dynamics, no fabricated market conditions. If
  something material is unknown, write that it is not yet clear and note it
  as something for MusperSolutions to probe.
- Never mention money amounts, prices, or fee levels anywhere. Pricing is
  MusperSolutions' alone.

VOICE:
- A sharp Rwandan business consultant writing for another consultant: direct,
  concrete, professional. Honest about weaknesses without being harsh; the
  goal is clarity the client can act on, not a verdict.
- Plain language. No em-dashes or dashes used as punctuation (use commas or
  periods). No emoji. No buzzwords, no consulting jargon, no clichés or AI
  filler like "delve", "landscape", "leverage", "holistic", "journey",
  "game-changer", "unlock", "robust", "navigate", "at the end of the day",
  "it's not just X, it's Y".
- Write in third person about the business ("the company", "{'{'}owner name{'}'}"),
  since MusperSolutions is the reader.

SERVICE LINES (recommend 1-3, each justified by the ROOT CAUSE):
- Business Development Consulting: strategy, market positioning, growth
  planning, financial discipline.
- Digital Transformation: digitising sales, operations, or customer channels;
  tools and systems adoption.
- Capacity-Building and Training: structured skills programs for teams or
  founders (including SIYB-style training).
- Coaching and Mentorship: sustained one-on-one work with the owner or
  leaders on how they run the business.
- Event Management: forums, convenings, B2B events (rarely the right
  prescription for an internal root cause; only when connecting to markets
  or peers IS the treatment).
- Premium Strategic Advisory: senior, high-touch advisory for complex or
  high-stakes situations (governance overhauls, investment readiness,
  turnarounds).

ENGAGEMENT TYPE (informed by the budget/timeline appetite answer):
- quick_consult: a short, focused engagement; fits a contained question or a
  client with minimal appetite.
- project: a defined piece of work over weeks to a few months.
- retainer_6_12: sustained 6 to 12 month accompaniment; fits deep root causes
  that need behaviour change over time, when the client's appetite supports it.
Respect the client's stated appetite; if the root cause needs more than they
signalled appetite for, choose the type matching their appetite and say in
next_step what a first slice would be.

THE SUMMARY COVER (the first thing the client reads):
- The headline scores, strongest and weakest areas, and priority areas are
  computed in code and given to you. Never restate them differently or
  invent other numbers.
- combined_headline and combined_body say what the combined result tells
  us. Lead with what the money habits reveal, then connect them to the
  rest of the picture. Plain, specific, grounded in the scores and answers.
  When Money Habits were not covered, lead with the strongest signal there is.
- For each priority area, write one concrete first step the client can take
  this week, adapted to what they actually said. Not a programme, a step.

OUTPUT: call the submit_report tool exactly once with every field filled.
No text outside the tool call.
"""


def _report_tool(priorities: list[dict[str, Any]], has_finance: bool) -> dict[str, Any]:
    """REPORT_TOOL plus the fields that depend on this interview: a summary
    per Money Habits category (when covered) and a first step per priority."""
    tool = json.loads(json.dumps(REPORT_TOOL))
    schema = tool["input_schema"]
    schema["properties"]["combined_headline"] = {
        "type": "string",
        "description": (
            "One bold sentence: what the combined result tells us. Leads with "
            "what the money habits reveal. Plain text, no numbers invented."
        ),
    }
    schema["properties"]["combined_body"] = {
        "type": "string",
        "description": (
            "Exactly 2 or 3 short sentences (never more) expanding the headline, "
            "grounded in the scores and the client's answers, connecting money "
            "habits to the wider picture."
        ),
    }
    schema["required"] += ["combined_headline", "combined_body"]
    if has_finance:
        schema["properties"]["finance_summaries"] = {
            "type": "object",
            "required": FINANCE_KEYS,
            "properties": {
                c["key"]: {
                    "type": "string",
                    "description": (
                        f"{c['name']}: 1-2 sentences summarising what the client "
                        "said about this money habit. The client will read this, "
                        "so no scores and no scoring notes."
                    ),
                }
                for c in FINANCE_CATEGORIES
            },
        }
        schema["required"].append("finance_summaries")
    if priorities:
        schema["properties"]["priority_steps"] = {
            "type": "object",
            "required": [p["key"] for p in priorities],
            "properties": {
                p["key"]: {
                    "type": "string",
                    "description": (
                        f"Priority: {p['name']} ({p['score']}/{p['max']}). One concrete "
                        "first step for this week, 1-2 sentences, adapted to what the "
                        "client said."
                        + (f" Build on this recommendation: {p['recommendation']}." if p.get("recommendation") else "")
                    ),
                }
                for p in priorities
            },
        }
        schema["required"].append("priority_steps")
    return tool


# ───────────────────── evidence pack assembly ─────────────────────

def _build_evidence_pack(state: dict[str, Any], transcript: list[Any]) -> str:
    """Assemble everything the analyst needs into one structured user message."""
    snap = state.get("snapshot", {})
    lines: list[str] = []

    lines.append("=== COMPANY SNAPSHOT ===")
    lines.append(f"Company: {snap.get('company_name') or 'not captured'}")
    lines.append(f"Sector: {snap.get('sector') or 'not captured'}")
    lines.append(f"Years in operation: {snap.get('years_in_operation') or 'not captured'}")
    lines.append(f"Team size: {snap.get('team_size') or 'not captured'}")
    lines.append(f"Revenue/budget range: {snap.get('revenue_range') or 'not captured'}")
    lines.append(
        f"Interviewee: {snap.get('person_name') or 'not captured'} "
        f"({snap.get('person_role') or 'role not captured'})"
    )

    lines.append("\n=== SCAN SCORES (1 = critical gap, 5 = strong) ===")
    scan = state.get("scan", {})
    for key in SCAN_AREA_KEYS:
        area = scan.get(key, {})
        name = SCAN_AREA_MAP[key]["name"]
        score = area.get("score")
        defaulted = " (defaulted, the answer was unclear)" if _is_defaulted(area) else ""
        lines.append(f"[{key}] {name}: {score if score is not None else 'not scored'}{defaulted}")
        if area.get("answer"):
            lines.append(f"    Client's answer: {area['answer']}")
        if area.get("rationale"):
            lines.append(f"    Interviewer's scoring note: {area['rationale']}")

    lines.append("\n=== MONEY HABITS (0 = critical gap, 3 = strong) ===")
    finance = state.get("finance") or {}
    if not any((finance.get(k) or {}).get("score") is not None for k in FINANCE_KEYS):
        lines.append("(not covered in this interview)")
    else:
        pct = financial_health_pct({k: (finance.get(k) or {}).get("score") for k in FINANCE_KEYS})
        lines.append(f"Financial health: {f'{pct}%' if pct is not None else 'incomplete'}")
        for cat in FINANCE_CATEGORIES:
            entry = finance.get(cat["key"]) or {}
            score = entry.get("score")
            unclear = " (answer stayed unclear)" if entry.get("unclear") else ""
            lines.append(f"[{cat['key']}] {cat['name']}: {score if score is not None else 'not scored'}{unclear}")
            if entry.get("answer"):
                lines.append(f"    Asked: {entry.get('question') or cat['anchor']}")
                lines.append(f"    Client's answer: {entry['answer']}")
            if entry.get("followup_answer"):
                lines.append(f"    Follow-up asked: {entry.get('followup_question')}")
                lines.append(f"    Client's answer: {entry['followup_answer']}")
            if entry.get("rationale"):
                lines.append(f"    Interviewer's scoring note: {entry['rationale']}")

    lines.append("\n=== BRANCH ANSWERS (only asked where the scan found weakness) ===")
    branch = state.get("branch", {})
    any_branch = False
    for key in state.get("branch_order", []):
        if branch.get(key):
            any_branch = True
            lines.append(f"[{key}] {SCAN_AREA_MAP[key]['name']}: {branch[key]}")
    if not any_branch:
        lines.append("(no areas scored low enough to trigger deeper questions)")

    lines.append("\n=== TRIANGULATION ===")
    tri = state.get("triangulate", {})
    for key in TRIANGULATE_KEYS:
        label = TRIANGULATE_LABELS.get(key, key)
        lines.append(f"{label}: {tri.get(key) or 'not captured'}")

    lines.append("\n=== COMPUTED IN CODE (use as given) ===")
    stored = _scores_json(state)
    pct = stored["financial_health_pct"]
    lines.append(f"Financial Health: {f'{pct}%' if pct is not None else 'not assessed'}")
    bh = business_health_pct(stored["scan"])
    lines.append(f"Business Health (Scan areas on 0-100): {f'{bh}%' if bh is not None else 'not assessed'}")
    priorities = priority_areas(stored["scan"], stored["finance"])
    if priorities:
        lines.append("Priority areas, weakest first:")
        for p in priorities:
            lines.append(f"  [{p['key']}] {p['name']}: {p['score']}/{p['max']}")
    else:
        lines.append("Priority areas: none scored weak enough to be a priority.")

    lines.append("\n=== FULL TRANSCRIPT ===")
    for m in transcript:
        speaker = "INTERVIEWER" if m.role == MessageRole.assistant else "CLIENT"
        lines.append(f"{speaker}: {m.content}")

    lines.append(
        "\nProduce the Root-Cause Diagnostic Report now by calling submit_report."
    )
    return "\n".join(lines)


# ───────────────────── Claude call ─────────────────────

def _call_report_model(evidence_pack: str, tool: dict[str, Any] = REPORT_TOOL) -> dict[str, Any]:
    """One forced-tool call. Returns the submit_report tool input as a dict.

    Same failure contract as the chatbot: friendly HTTPException, specifics
    to the server log only, no user content or secrets logged.
    """
    client = _get_client().with_options(timeout=settings.claude_report_timeout_seconds)
    try:
        import anthropic  # type: ignore

        try:
            response = client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.claude_report_max_tokens,
                system=SYSTEM_PROMPT,
                tools=[tool],
                tool_choice={"type": "tool", "name": "submit_report"},
                messages=[{"role": "user", "content": evidence_pack}],
            )
        except anthropic.RateLimitError as exc:
            log.warning("Report gen rate limited (request_id=%s)", getattr(exc, "request_id", "?"))
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=_BUSY_MSG) from exc
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as exc:
            log.warning("Report gen: Anthropic unreachable: %s", type(exc).__name__)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=_RETRY_MSG) from exc
        except anthropic.APIStatusError as exc:
            log.error(
                "Report gen: Anthropic API error %s (status=%s, request_id=%s)",
                type(exc).__name__, getattr(exc, "status_code", "?"), getattr(exc, "request_id", "?"),
            )
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_RETRY_MSG) from exc
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Report gen: unexpected failure (%s)", type(exc).__name__)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_RETRY_MSG) from exc

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "submit_report":
            try:
                return dict(block.input)
            except Exception:
                return json.loads(block.input)  # type: ignore[arg-type]

    log.error("Report gen: model returned no submit_report tool call.")
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=_RETRY_MSG)



# Emoji and pictographs: never in a report (the PDF fonts cannot draw them).
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]")


def _sanitize(value):
    """Scrub typographic AI-tells from generated text, recursively: em and en
    dashes, spaced hyphens used as dashes, curly quotes, and emoji."""
    if isinstance(value, str):
        value = _EMOJI.sub("", value)
        value = re.sub(r"\s+[\u2014\u2013]\s+|\s+-\s+(?=[A-Za-z])", ", ", value)
        return (value.replace("\u2014", ", ").replace("\u2013", "-")
                     .replace("\u201c", '"').replace("\u201d", '"')
                     .replace("\u2018", "'").replace("\u2019", "'")
                     .replace(" ,", ",").replace(",,", ",").strip())
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    return value


# ───────────────────── persistence ─────────────────────

DEFAULTED_NOTE = (
    "The answer in this area was unclear, so it was given a neutral score "
    "of 3 for MusperSolutions to confirm with you."
)
NO_SUMMARY = "The client did not clearly address this area during the interview."


def _is_defaulted(area: dict[str, Any]) -> bool:
    """True when the area's score is the clarification default rather than a
    real reading. States saved before the `defaulted` flag existed are
    inferred: no score at all, or a 3 with no recorded answer."""
    if area.get("defaulted"):
        return True
    score = area.get("score")
    return score is None or (score == 3 and not (area.get("answer") or "").strip())


def _scores_json(
    state: dict[str, Any],
    summaries: dict[str, Any] | None = None,
    finance_summaries: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Scan scores + a 0-100 aggregate so every legacy list/dashboard reader
    (which expects grow_overall/band) keeps working without changes.

    Every area A-F always carries a name, a score and a summary, so no
    renderer ever has an empty section. `rationale` is advisor-only and is
    stripped from client payloads in dashboard._report_payload."""
    summaries = summaries or {}
    scan_out: dict[str, Any] = {}
    scored: list[int] = []
    for key in SCAN_AREA_KEYS:
        area = (state.get("scan") or {}).get(key) or {}
        defaulted = _is_defaulted(area)
        score = 3 if area.get("score") is None else int(area["score"])
        summary = (
            (summaries.get(key) or "").strip()
            or (area.get("answer") or "").strip()
            or NO_SUMMARY
        )
        scan_out[key] = {
            "name": SCAN_AREA_MAP[key]["name"],
            "score": score,
            "summary": summary,
            "defaulted": defaulted,
            "note": DEFAULTED_NOTE if defaulted else None,
            "rationale": area.get("rationale"),
        }
        scored.append(score)

    aggregate = round(sum(scored) / len(scored) * 20, 1) if scored else 0.0
    finance_out, health_pct = _finance_scores(state, finance_summaries)
    return {
        "report_type": REPORT_TYPE,
        "scan": scan_out,
        # Money Habits. Empty / None on sessions from before the stage existed.
        "finance": finance_out,
        "financial_health_pct": health_pct,
        "finance_followups": list(state.get("finance_followups") or []),
        # Legacy-reader compatibility (client lists, session summaries, stats):
        "grow_overall": aggregate,
        "grow_band": band_for(aggregate),
        "finance_readiness": aggregate,
        "finance_band": band_for(aggregate),
    }


def _finance_scores(
    state: dict[str, Any], summaries: dict[str, Any] | None = None
) -> tuple[dict[str, Any], int | None]:
    """Money Habits scores for the report. `rationale` is advisor-only and is
    stripped from client payloads in dashboard._report_payload. The health
    percentage is computed here in code, never by the model."""
    finance = state.get("finance") or {}
    if not any((finance.get(k) or {}).get("score") is not None for k in FINANCE_KEYS):
        return {}, None
    out: dict[str, Any] = {}
    for cat in FINANCE_CATEGORIES:
        entry = finance.get(cat["key"]) or {}
        out[cat["key"]] = {
            "name": cat["name"],
            "score": entry.get("score"),
            "unclear": bool(entry.get("unclear")),
            "followed_up": cat["key"] in (state.get("finance_followups") or []),
            "summary": ((summaries or {}).get(cat["key"]) or "").strip()
            or (entry.get("answer") or "").strip()
            or "The client did not clearly address this during the interview.",
            "rationale": entry.get("rationale"),
        }
    pct = financial_health_pct({k: out[k]["score"] for k in FINANCE_KEYS})
    return out, pct


def _first_sentences(text: str, limit: int) -> str:
    """Keep the combined statement to its brief: at most `limit` sentences."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\"'])", text.strip())
    return " ".join(parts[:limit]).strip()


def _content_json(
    state: dict[str, Any], analysis: dict[str, Any], priorities: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    snap = state.get("snapshot", {})
    engagement_in = analysis.get("engagement") or {}
    eng_type = engagement_in.get("type")
    if eng_type not in ENGAGEMENT_TYPES:
        eng_type = "project"
    return {
        "report_type": REPORT_TYPE,
        # `summary` doubles as the card blurb in existing list UIs.
        "summary": analysis.get("headline") or "",
        "combined": {
            "headline": analysis.get("combined_headline") or analysis.get("headline") or "",
            "body": _first_sentences(analysis.get("combined_body") or "", 3),
        },
        # Chosen in code (report_summary.priority_areas); the model only
        # writes the first step for each.
        "priorities": [
            {**p, "first_step": ((analysis.get("priority_steps") or {}).get(p["key"]) or "").strip()
             or p.get("recommendation") or "Agree the first step with MusperSolutions."}
            for p in (priorities or [])
        ],
        "snapshot": {
            "company_name": snap.get("company_name"),
            "sector": snap.get("sector"),
            "years_in_operation": snap.get("years_in_operation"),
            "team_size": snap.get("team_size"),
            "revenue_range": snap.get("revenue_range"),
            "person_name": snap.get("person_name"),
            "person_role": snap.get("person_role"),
        },
        "diagnosis": {
            "presenting_problem": analysis.get("presenting_problem") or "",
            "root_cause": analysis.get("root_cause") or "",
            "root_cause_evidence": analysis.get("root_cause_evidence") or [],
            "already_tried": analysis.get("already_tried") or [],
            "ownership": analysis.get("ownership") or "",
        },
        "service_pathway": analysis.get("service_pathway") or [],
        "engagement": {
            "type": eng_type,
            "type_label": ENGAGEMENT_LABELS[eng_type],
            "timeline": engagement_in.get("timeline") or "To be scoped with MusperSolutions",
            # Never model-generated; MusperSolutions edits this after review.
            "investment_range": INVESTMENT_PLACEHOLDER,
            "next_step": engagement_in.get("next_step") or "MusperSolutions will follow up to schedule a scoping conversation.",
        },
    }


def generate_report(db: Session, session: DiagnosticSession) -> Report:
    """Generate (or regenerate) the report for a completed session.

    Regeneration updates the existing report row in place, preserving its
    is_shared flag, so a shared report stays shared after a re-run.
    """
    if session.status != SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A report can only be generated for a completed diagnostic.",
        )
    state = session.diagnostic_state or {}
    if not state.get("scan"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This session has no diagnostic data to analyse.",
        )

    transcript = sorted(session.messages, key=lambda m: m.created_at)
    evidence = _build_evidence_pack(state, transcript)
    # Scores do not depend on the model, so priorities come from exactly
    # what the report will store.
    stored = _scores_json(state)
    has_finance = bool(stored["finance"])
    priorities = priority_areas(stored["scan"], stored["finance"])
    analysis = _sanitize(_call_report_model(evidence, _report_tool(priorities, has_finance)))

    scores = _scores_json(state, analysis.get("scan_summaries"), analysis.get("finance_summaries"))
    content = _content_json(state, analysis, priorities)

    existing = db.scalar(
        select(Report)
        .where(Report.session_id == session.id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    if existing is not None:
        existing.scores_json = scores
        existing.content_json = content
        db.add(existing)
        db.commit()
        db.refresh(existing)
        log.info("Regenerated report %s for session %s", existing.id, session.id)
        return existing

    report = Report(session_id=session.id, scores_json=scores, content_json=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    log.info("Generated report %s for session %s", report.id, session.id)
    return report


def generate_report_for_session(session_id: uuid.UUID) -> None:
    """Background-task entry point (own DB session, never raises).

    Used for auto-generation the moment an interview completes. Any failure
    is logged and left for the advisor's manual regenerate endpoint.
    """
    db = SessionLocal()
    try:
        session = db.scalar(
            select(DiagnosticSession)
            .options(selectinload(DiagnosticSession.messages))
            .where(DiagnosticSession.id == session_id)
        )
        if session is None:
            log.error("Auto report gen: session %s not found.", session_id)
            return
        generate_report(db, session)
    except Exception as exc:
        # Deliberate catch-all: a report failure must never break the
        # interview completion path. MusperSolutions can regenerate manually.
        log.error(
            "Auto report gen failed for session %s (%s). "
            "Advisor can regenerate from the dashboard.",
            session_id, type(exc).__name__,
        )
    finally:
        db.close()
