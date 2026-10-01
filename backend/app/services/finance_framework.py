"""Money Habits: MusperSolutions' financial diagnostic framework.

Single source of truth for the Money Habits interview stage: the eight
categories, the anchor question and follow-ups for each, the 0-3 scoring
rubric, and the recommendation that goes with each score. The interview
(diagnostic_chatbot) and the report (report_generator, and the report views)
all read from here.

Condensed format: one anchor question per category, scored 0-3 against the
rubric. Only a score of 0 or 1 earns ONE follow-up, after which the category
score is final.
"""
from __future__ import annotations

import math
from typing import Any

FINANCE_CATEGORIES: list[dict[str, Any]] = [
    {
        "key": "awareness",
        "name": "Financial Awareness and Record-Keeping",
        "anchor": (
            "Do you know your exact revenue and expenses from last month, or "
            "would you need to check somewhere?"
        ),
        "followups": [
            "How do you currently track income and expenses (spreadsheet, app, "
            "notebook, nothing formal)?",
            "Can you tell me your profit margin off the top of your head?",
        ],
        "rubric": {
            0: "No idea, no tracking",
            1: "Rough idea, inconsistent tracking",
            2: "Tracks regularly but does not analyse",
            3: "Knows the numbers and uses them to decide",
        },
        "recommendations": {
            0: "Set up basic bookkeeping, even a simple spreadsheet, before anything else",
            1: "Build a weekly money check-in habit and use a simple accounting tool such as Wave",
            2: "Add a monthly profit and loss review",
            3: "Move on to forecasting and deeper analysis",
        },
    },
    {
        "key": "cash_flow",
        "name": "Cash Flow",
        "anchor": (
            "Has there been a month in the last year where you could not pay a "
            "bill on time? What happened?"
        ),
        "followups": [
            "Do you know how many days, on average, customers take to pay you?",
            "If a big client paid you 60 days late, would the business survive?",
        ],
        "rubric": {
            0: "Regularly cannot pay bills, no idea of payment timing",
            1: "Occasional crunches, unaware of how long customers take to pay",
            2: "Stable but tight",
            3: "Consistently smooth",
        },
        "recommendations": {
            0: "Build a 13-week cash flow forecast and renegotiate client payment terms",
            1: "Track how long customers take to pay and use invoicing with automatic reminders",
            2: "Build a one-month cash buffer",
            3: "Put surplus cash to work in short-term savings",
        },
    },
    {
        "key": "pricing",
        "name": "Pricing and Profitability",
        "anchor": (
            "How did you decide on your current prices: gut feeling, matching "
            "competitors, or an actual cost calculation?"
        ),
        "followups": [
            "Do you know your cost per product or service, including your own time?",
            "Which product or service makes you the most money, and which one "
            "might be losing you money?",
        ],
        "rubric": {
            0: "Prices by gut, true costs unknown",
            1: "Copies competitors, no margin analysis",
            2: "Cost-aware but no recent pricing review",
            3: "Data-driven pricing",
        },
        "recommendations": {
            0: "Run a cost-per-unit exercise immediately",
            1: "Do a margin review for each product or service line",
            2: "Set an annual pricing review",
            3: "Test premium tiers or value-based pricing",
        },
    },
    {
        "key": "debt",
        "name": "Debt and Financing",
        "anchor": (
            "Have you ever mixed personal and business money? How often does "
            "that happen?"
        ),
        "followups": [
            "What debt does the business carry right now, and what interest rate "
            "is on each?",
            "If you suddenly needed a large sum for the business tomorrow, where "
            "would it come from?",
        ],
        "rubric": {
            0: "Expensive debt and constant mixing of funds",
            1: "Some mixing, unclear on debt terms",
            2: "Organised but no repayment plan",
            3: "Clean structure",
        },
        "recommendations": {
            0: "Separate business and personal accounts immediately and pay down the most expensive debt first",
            1: "Open a dedicated business account and list every debt with its rate",
            2: "Create a structured repayment schedule",
            3: "Consider strategic financing to fund growth",
        },
    },
    {
        "key": "reserves",
        "name": "Savings, Reserves and Risk",
        "anchor": (
            "If the business made zero income for two months, how long could "
            "you keep operating?"
        ),
        "followups": [
            "Do you set money aside for taxes, or does it come out of whatever is left?",
            "What is your plan if your biggest customer left tomorrow?",
        ],
        "rubric": {
            0: "No reserve, no tax fund, no contingency",
            1: "Some savings, no target",
            2: "Reserve exists but untested",
            3: "Solid reserves and a contingency plan",
        },
        "recommendations": {
            0: "Set aside a fixed share of income for taxes and start an emergency fund",
            1: "Set a reserve target, for example three months of operating costs",
            2: "Stress-test the business with what-if scenarios",
            3: "Keep reserves in an interest-earning account",
        },
    },
    {
        "key": "growth",
        "name": "Growth and Planning",
        "anchor": (
            "Do you have a specific revenue goal for this year, and how did you "
            "arrive at that number?"
        ),
        "followups": [
            "What is stopping you from doubling revenue right now: money, time, "
            "demand, or something else?",
            "If an unexpected sum of money came in, would you reinvest it, save "
            "it, or use it to catch up on something?",
        ],
        "rubric": {
            0: "No goals, purely reactive",
            1: "Vague goals with no numbers",
            2: "Goals but unclear on constraints",
            3: "Clear goals and a growth plan",
        },
        "recommendations": {
            0: "Set one concrete 90-day revenue goal with a simple plan",
            1: "Build a basic revenue and growth projection",
            2: "Identify the single biggest bottleneck to growth",
            3: "Explore a scaling strategy or outside investment",
        },
    },
    {
        "key": "mindset",
        "name": "Mindset and Support",
        "anchor": (
            "On a scale of 1 to 10, how confident do you feel making financial "
            "decisions for the business?"
        ),
        "followups": [
            "Who do you currently go to for financial advice, if anyone?",
            "What is the last financial decision you made that you are still "
            "unsure was right?",
        ],
        "rubric": {
            0: "Low confidence, no advisor, avoids decisions",
            1: "Some confidence, no consistent support",
            2: "Confident but isolated",
            3: "Confident and supported",
        },
        "recommendations": {
            0: "Regular advisor check-ins and simpler tools",
            1: "Connect with a bookkeeper or mentor",
            2: "Join a peer group for accountability",
            3: "Focus advisory time on strategic questions",
        },
    },
    {
        "key": "compliance",
        "name": "Compliance, Systems and Exit Readiness",
        "anchor": "Are your taxes and required filings currently up to date?",
        "followups": [
            "If you wanted to sell the business in five years, could you hand "
            "someone clean financial records today?",
            "Do you have business insurance, and what would happen financially "
            "if you could not work for a month?",
        ],
        "rubric": {
            0: "Filings behind, no insurance, records unusable",
            1: "Mostly compliant but disorganised records",
            2: "Compliant but records not ready for a buyer",
            3: "Compliant, insured, records ready for a buyer",
        },
        "recommendations": {
            0: "Catch up on compliance and basic insurance before any growth work",
            1: "Book a compliance and insurance review with a professional",
            2: "Document processes and clean up records every year",
            3: "Consider formal succession or exit planning",
        },
    },
]

FINANCE_KEYS: list[str] = [c["key"] for c in FINANCE_CATEGORIES]
FINANCE_MAP: dict[str, dict[str, Any]] = {c["key"]: c for c in FINANCE_CATEGORIES}

MAX_SCORE = 3
# A category scoring at or below this earns one follow-up question.
FOLLOWUP_THRESHOLD = 1
# Score given when the answer stays unclear after the one clarification.
# A vague answer about money is itself a signal, so it counts as weak.
UNCLEAR_SCORE = 1


def needs_followup(score: int | None) -> bool:
    return score is not None and score <= FOLLOWUP_THRESHOLD


def recommendation_for(key: str, score: int | None) -> str | None:
    if score is None:
        return None
    return FINANCE_MAP[key]["recommendations"].get(int(score))


def financial_health_pct(scores: dict[str, int | None]) -> int | None:
    """round(sum of the 8 category scores / 24 x 100). Computed in code, never
    by the model. None unless every category has a score (older sessions, or
    an interview closed by the turn cap before Money Habits finished)."""
    values = [scores.get(k) for k in FINANCE_KEYS]
    if any(v is None for v in values):
        return None
    # Round half up (15/24 = 62.5% -> 63%). Python's round() would give 62.
    return math.floor(sum(int(v) for v in values) * 100 / (len(FINANCE_KEYS) * MAX_SCORE) + 0.5)
