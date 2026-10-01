"""Client teaser snapshot: the small taste of results a client sees the moment
their interview completes, before Penny shares the full report.

Deterministic, no AI call: computed straight from diagnostic_state using the
same scoring as the report, so the numbers always match it.

Privacy rule: the response is built field by field from an explicit
allowlist below. It is never produced by taking a larger object (a report
payload, the state) and filtering keys out, so a new field added elsewhere
can never leak through here.
"""
from __future__ import annotations

from typing import Any

from app.models.diagnostic_session import DiagnosticSession, SessionStatus
from app.services import report_summary
from app.services.report_generator import _scores_json

# What the full report contains, shown to the client as locked items only.
LOCKED_SECTIONS: list[str] = [
    "Money habits breakdown",
    "Root cause diagnosis",
    "Priority actions",
    "Recommendations",
]
SHARE_NOTE = "Penny will share your full report with you once she has reviewed it."


def _score(headline: dict[str, Any]) -> dict[str, Any]:
    return {
        "pct": headline["pct"],
        "band": headline["band"],
        "band_label": headline["band_label"],
        "assessed": headline["assessed"],
    }


def build_teaser(session: DiagnosticSession) -> dict[str, Any]:
    """The allowlisted teaser for a COMPLETED session. Caller checks status
    and ownership."""
    if session.status != SessionStatus.completed:
        raise ValueError("The teaser only exists once the interview is complete.")
    state = session.diagnostic_state or {}
    has_scan = any((v or {}).get("score") is not None for v in (state.get("scan") or {}).values())
    # Numbers only are read from this. Sessions with no Scan data (seeded or
    # legacy) stay "not assessed" rather than showing the report's defaults.
    scores = _scores_json(state) if has_scan else {}
    summary = report_summary.build_summary(scores, {})
    latest = max(session.reports, key=lambda r: r.created_at) if session.reports else None
    shared = bool(latest and latest.is_shared)
    return {
        "session_id": session.id,
        "completed_at": session.completed_at,
        "financial_health": _score(summary["financial_health"]),
        "business_health": _score(summary["business_health"]),
        "strongest_area": summary["strongest"]["name"] if summary["strongest"] else None,
        "attention_area": summary["weakest"]["name"] if summary["weakest"] else None,
        "locked_sections": list(LOCKED_SECTIONS),
        "share_note": SHARE_NOTE,
        "report_shared": shared,
        # Only revealed once shared, so the client can open the full report.
        "report_id": latest.id if shared else None,
    }
