"""Deterministic summary layer for the Root-Cause Diagnostic Report.

Headline scores, bands, strongest / weakest area and the priority areas are
all computed here in code from the stored scores, never by the model. The
model only writes words around them (the combined result statement and one
first step per priority). Both the web report and the PDF read the result,
so they always agree.
"""
from __future__ import annotations

import math
from typing import Any

from app.core.scoring import NOT_ASSESSED, band_for, band_label
from app.services.diagnostic_chatbot import SCAN_AREA_KEYS, SCAN_AREA_MAP
from app.services.finance_framework import FINANCE_CATEGORIES, recommendation_for

MAX_PRIORITIES = 3
# Weak enough to be a priority: finance 0-1 (of 3), Scan 1-2 (of 5).
FINANCE_PRIORITY_MAX = 1
SCAN_PRIORITY_MAX = 2

NEXT_STEPS: list[dict[str, str]] = [
    {
        "title": "Read and reflect",
        "detail": "Go through this report on your own first. Note what rings true and what surprised you.",
    },
    {
        "title": "Pick one action to start this week",
        "detail": "Choose a single priority action from this report and take its first step in the next seven days.",
    },
    {
        "title": "Book a session with Penny",
        "detail": "Talk the findings through with Penny at MusperSolutions and agree what to tackle together.",
    },
]


def _round_half_up(value: float) -> int:
    return math.floor(value + 0.5)


def business_health_pct(scan: dict[str, Any]) -> int | None:
    """The six Scan areas rescaled from 1-5 to 0-100: (average - 1) / 4 x 100."""
    scores = [(scan.get(k) or {}).get("score") for k in SCAN_AREA_KEYS]
    scores = [int(s) for s in scores if s is not None]
    if not scores:
        return None
    return _round_half_up((sum(scores) / len(scores) - 1) / 4 * 100)


def _headline(pct: int | None) -> dict[str, Any]:
    band = band_for(pct) if pct is not None else None
    return {
        "pct": pct,
        "assessed": pct is not None,
        "band": band,
        "band_label": band_label(band) if band else NOT_ASSESSED,
    }


def _areas(scan: dict[str, Any], finance: dict[str, Any]) -> list[dict[str, Any]]:
    """Every scored area on one 0-100 scale. Finance first, so that when two
    areas tie, the money habit wins (it leads the report)."""
    out: list[dict[str, Any]] = []
    for cat in FINANCE_CATEGORIES:
        score = (finance.get(cat["key"]) or {}).get("score")
        if score is not None:
            out.append({"kind": "finance", "key": cat["key"], "name": cat["name"],
                        "score": int(score), "max": 3, "pct": _round_half_up(int(score) / 3 * 100)})
    for key in SCAN_AREA_KEYS:
        score = (scan.get(key) or {}).get("score")
        if score is not None:
            out.append({"kind": "scan", "key": key, "name": SCAN_AREA_MAP[key]["name"],
                        "score": int(score), "max": 5, "pct": _round_half_up((int(score) - 1) / 4 * 100)})
    return out


def priority_areas(scan: dict[str, Any], finance: dict[str, Any]) -> list[dict[str, Any]]:
    """The 2-3 weakest areas overall: finance categories scoring 0-1 and Scan
    areas scoring 1-2, weakest first, finance first when tied."""
    weak = [
        a for a in _areas(scan, finance)
        if (a["kind"] == "finance" and a["score"] <= FINANCE_PRIORITY_MAX)
        or (a["kind"] == "scan" and a["score"] <= SCAN_PRIORITY_MAX)
    ]
    weak.sort(key=lambda a: (a["pct"], 0 if a["kind"] == "finance" else 1))  # stable
    out = []
    for a in weak[:MAX_PRIORITIES]:
        entry = dict(a)
        if a["kind"] == "finance":
            entry["recommendation"] = recommendation_for(a["key"], a["score"])
        out.append(entry)
    return out


def build_summary(scores: dict[str, Any], content: dict[str, Any]) -> dict[str, Any]:
    """Everything the summary cover needs, from a report's stored JSON.
    Reports from before Money Habits existed get 'Not assessed' for
    Financial Health and simply leave the finance parts out."""
    scan = scores.get("scan") or {}
    finance = scores.get("finance") or {}
    areas = _areas(scan, finance)
    strongest = max(areas, key=lambda a: a["pct"]) if areas else None  # first max = finance on ties
    weakest = min(areas, key=lambda a: a["pct"]) if areas else None
    combined = content.get("combined") or {}
    return {
        "financial_health": _headline(scores.get("financial_health_pct")),
        "business_health": _headline(business_health_pct(scan)),
        "strongest": strongest,
        "weakest": weakest,
        "combined": {
            # Older reports have no combined statement; their headline stands in.
            "headline": combined.get("headline") or content.get("summary") or "",
            "body": combined.get("body") or "",
        },
    }


def finance_rows(finance: dict[str, Any]) -> list[dict[str, Any]]:
    """Money Habits rows for display, in framework order, each with the
    recommendation for its score read from finance_framework."""
    rows = []
    for cat in FINANCE_CATEGORIES:
        entry = finance.get(cat["key"]) or {}
        score = entry.get("score")
        row = {
            "key": cat["key"],
            "name": cat["name"],
            "score": score,
            "summary": entry.get("summary") or "",
            "recommendation": recommendation_for(cat["key"], score),
            "unclear": bool(entry.get("unclear")),
            "weak": score is not None and score <= FINANCE_PRIORITY_MAX,
        }
        if "rationale" in entry:  # advisor payloads only; stripped upstream for clients
            row["rationale"] = entry["rationale"]
        rows.append(row)
    return rows


def financial_health_row(fh: dict[str, Any]) -> dict[str, Any]:
    """Scan Results row G: points the reader to the Money Habits section."""
    if fh["assessed"]:
        summary = (
            "The combined score of the eight money habits. "
            "See Money Habits for the full breakdown and what to do next."
        )
    else:
        summary = "Money habits were not covered in this interview."
    return {"key": "G", "name": "Financial Health", **fh, "summary": summary}

