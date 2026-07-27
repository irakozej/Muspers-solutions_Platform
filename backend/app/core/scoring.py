"""Scoring helpers for the Hatana-style diagnostic.

Five GROW domains, each 0-100. Two composite headline scores:
  - GROW Overall         = simple mean across all five domains
  - Finance Readiness    = weighted toward Money + Operations + Strategy
Bands: A ≥ 80 · B 60-79 · C < 60.
"""
from __future__ import annotations

DOMAINS: tuple[str, ...] = ("strategy", "customers", "money", "operations", "talent")

# Weights for the Finance Readiness composite (sum to 1).
FINANCE_READINESS_WEIGHTS: dict[str, float] = {
    "money": 0.45,
    "operations": 0.25,
    "strategy": 0.15,
    "customers": 0.10,
    "talent": 0.05,
}


def band_for(score: float | int | None) -> str:
    if score is None:
        return "-"
    if score >= 80:
        return "A"
    if score >= 60:
        return "B"
    return "C"


def grow_overall(domain_scores: dict[str, float | int]) -> float:
    values = [float(domain_scores[d]) for d in DOMAINS if d in domain_scores]
    return round(sum(values) / len(values), 1) if values else 0.0


def finance_readiness(domain_scores: dict[str, float | int]) -> float:
    total = 0.0
    weight_total = 0.0
    for domain, weight in FINANCE_READINESS_WEIGHTS.items():
        if domain in domain_scores:
            total += float(domain_scores[domain]) * weight
            weight_total += weight
    return round(total / weight_total, 1) if weight_total else 0.0


def headline(domain_scores: dict[str, float | int]) -> dict[str, float | str]:
    grow = grow_overall(domain_scores)
    finance = finance_readiness(domain_scores)
    return {
        "grow_overall": grow,
        "grow_band": band_for(grow),
        "finance_readiness": finance,
        "finance_band": band_for(finance),
    }
