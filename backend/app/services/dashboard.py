"""Query helpers for the advisor + client dashboards."""
from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.scoring import band_for
from app.models.advisor_note import AdvisorNote
from app.models.chat_message import ChatMessage
from app.models.client import Client
from app.models.diagnostic_session import DiagnosticSession, SessionStatus
from app.models.rating import Rating
from app.models.report import Report
from app.models.user import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ───────────────────── advisor: aggregates ─────────────────────

def collect_advisor_stats(db: Session) -> dict:
    total_clients = db.scalar(select(func.count()).select_from(Client)) or 0
    week_ago = _now() - timedelta(days=7)
    active_sessions_this_week = (
        db.scalar(
            select(func.count())
            .select_from(DiagnosticSession)
            .where(DiagnosticSession.started_at >= week_ago)
        )
        or 0
    )
    completed_sessions = (
        db.scalar(
            select(func.count())
            .select_from(DiagnosticSession)
            .where(DiagnosticSession.status == SessionStatus.completed)
        )
        or 0
    )
    # Average GROW Overall across the latest report per session.
    grow_avg_row = db.execute(
        select(func.avg(Report.scores_json["grow_overall"].as_float()))
    ).scalar()
    average_grow_overall = round(float(grow_avg_row), 1) if grow_avg_row else 0.0
    reports_pending_share = (
        db.scalar(select(func.count()).select_from(Report).where(Report.is_shared.is_(False)))
        or 0
    )

    return {
        "total_clients": total_clients,
        "active_sessions_this_week": active_sessions_this_week,
        "completed_sessions": completed_sessions,
        "average_grow_overall": average_grow_overall,
        "reports_pending_share": reports_pending_share,
        "recent_activity": collect_recent_activity(db, limit=10),
    }


def collect_recent_activity(db: Session, *, limit: int) -> list[dict]:
    events: list[dict] = []

    for c in db.scalars(
        select(Client).options(selectinload(Client.user)).order_by(desc(Client.created_at)).limit(limit)
    ):
        events.append(
            {
                "kind": "client_registered",
                "title": f"New client: {c.business_name}",
                "description": c.sector,
                "at": c.created_at,
                "client_id": c.id,
                "session_id": None,
            }
        )

    completed = db.scalars(
        select(DiagnosticSession)
        .options(selectinload(DiagnosticSession.client))
        .where(DiagnosticSession.status == SessionStatus.completed)
        .order_by(desc(DiagnosticSession.completed_at))
        .limit(limit)
    )
    for s in completed:
        bn = s.client.business_name if s.client else "Unknown"
        events.append(
            {
                "kind": "diagnostic_completed",
                "title": f"Diagnostic complete: {bn}",
                "description": "Report generated, awaiting share decision",
                "at": s.completed_at or s.started_at,
                "client_id": s.client_id,
                "session_id": s.id,
            }
        )

    for r in db.scalars(
        select(Rating)
        .options(selectinload(Rating.session).selectinload(DiagnosticSession.client))
        .order_by(desc(Rating.created_at))
        .limit(limit)
    ):
        bn = r.session.client.business_name if r.session and r.session.client else "Unknown"
        events.append(
            {
                "kind": "rating_received",
                "title": f"Rating from {bn}",
                "description": f"{r.score} / 5 — {(r.feedback or '')[:80]}",
                "at": r.created_at,
                "client_id": r.session.client_id if r.session else None,
                "session_id": r.session_id,
            }
        )

    events.sort(key=lambda e: e["at"], reverse=True)
    return events[:limit]


# ───────────────────── advisor: client list ─────────────────────

def list_clients(
    db: Session, *, search: str | None = None, sector: str | None = None
) -> list[dict]:
    stmt = select(Client).options(
        selectinload(Client.user),
        selectinload(Client.diagnostic_sessions).selectinload(DiagnosticSession.reports),
    )
    if search:
        stmt = stmt.where(Client.business_name.ilike(f"%{search}%"))
    if sector:
        stmt = stmt.where(Client.sector == sector)
    stmt = stmt.order_by(Client.business_name)

    out: list[dict] = []
    for c in db.scalars(stmt):
        latest_session = max(
            c.diagnostic_sessions or [],
            key=lambda s: s.started_at,
            default=None,
        )
        latest_report = None
        if latest_session and latest_session.reports:
            latest_report = max(latest_session.reports, key=lambda r: r.created_at)

        scores = latest_report.scores_json if latest_report else None
        out.append(
            {
                "id": c.id,
                "business_name": c.business_name,
                "sector": c.sector,
                "location": c.location,
                "business_size": c.business_size.value if c.business_size else None,
                "employee_count": c.employee_count,
                "overall_score": float(scores["grow_overall"]) if scores else None,
                "band": band_for(scores["grow_overall"]) if scores else None,
                "finance_readiness": float(scores["finance_readiness"]) if scores else None,
                "last_activity": (latest_session.completed_at or latest_session.started_at)
                if latest_session
                else c.created_at,
                "session_status": latest_session.status.value if latest_session else None,
                "is_shared": bool(latest_report.is_shared) if latest_report else False,
                "has_report": latest_report is not None,
            }
        )
    return out


# ───────────────────── advisor: single client detail ─────────────────────

def client_detail(db: Session, client_id: uuid.UUID) -> dict | None:
    client = db.scalar(
        select(Client)
        .options(
            selectinload(Client.user),
            selectinload(Client.diagnostic_sessions).selectinload(DiagnosticSession.messages),
            selectinload(Client.diagnostic_sessions).selectinload(DiagnosticSession.reports),
            selectinload(Client.diagnostic_sessions).selectinload(DiagnosticSession.ratings),
            selectinload(Client.advisor_notes),
        )
        .where(Client.id == client_id)
    )
    if client is None:
        return None

    sessions = sorted(client.diagnostic_sessions, key=lambda s: s.started_at, reverse=True)
    latest = sessions[0] if sessions else None
    latest_report = None
    if latest and latest.reports:
        latest_report = max(latest.reports, key=lambda r: r.created_at)

    transcript = sorted(latest.messages, key=lambda m: m.created_at) if latest else []
    rating = latest.ratings[0] if latest and latest.ratings else None

    return {
        "id": client.id,
        "business_name": client.business_name,
        "sector": client.sector,
        "location": client.location,
        "business_size": client.business_size.value if client.business_size else None,
        "employee_count": client.employee_count,
        "founded_year": client.founded_year,
        "revenue_band": client.revenue_band,
        "revenue_trend": client.revenue_trend,
        "contact_email": client.user.email if client.user else None,
        "contact_name": client.user.full_name if client.user else None,
        "created_at": client.created_at,
        "sessions": [_session_summary(s) for s in sessions],
        "latest_report": _report_payload(latest_report, session_id=latest.id) if latest_report else None,
        "transcript": transcript,
        "rating": rating,
        "notes": client.advisor_notes,
    }


def _session_summary(session: DiagnosticSession) -> dict:
    report = max(session.reports, key=lambda r: r.created_at) if session.reports else None
    scores = report.scores_json if report else None
    rating = session.ratings[0] if session.ratings else None
    return {
        "id": session.id,
        "status": session.status.value,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "overall_score": float(scores["grow_overall"]) if scores else None,
        "band": band_for(scores["grow_overall"]) if scores else None,
        "is_shared": bool(report.is_shared) if report else False,
        "rating_score": rating.score if rating else None,
    }


def _report_payload(report: Report, *, session_id: uuid.UUID) -> dict:
    scores = report.scores_json or {}
    content = report.content_json or {}
    return {
        "id": report.id,
        "session_id": session_id,
        "headline": {
            "grow_overall": float(scores.get("grow_overall", 0)),
            "grow_band": scores.get("grow_band", band_for(scores.get("grow_overall"))),
            "finance_readiness": float(scores.get("finance_readiness", 0)),
            "finance_band": scores.get(
                "finance_band", band_for(scores.get("finance_readiness"))
            ),
        },
        "domains": {
            "strategy": float(scores.get("strategy", 0)),
            "customers": float(scores.get("customers", 0)),
            "money": float(scores.get("money", 0)),
            "operations": float(scores.get("operations", 0)),
            "talent": float(scores.get("talent", 0)),
        },
        "summary": content.get("summary"),
        "red_flags": content.get("red_flags", []),
        "priority_actions": content.get("priority_actions", []),
        "suggested_topics": content.get("suggested_topics", []),
        "is_shared": bool(report.is_shared),
        "created_at": report.created_at,
    }


# ───────────────────── advisor: analytics ─────────────────────

DOMAINS = ("strategy", "customers", "money", "operations", "talent")


def collect_analytics(db: Session) -> dict:
    reports = list(db.scalars(select(Report)))

    domain_totals = {d: 0.0 for d in DOMAINS}
    domain_counts = {d: 0 for d in DOMAINS}
    red_flags_counter: Counter = Counter()

    for r in reports:
        scores = r.scores_json or {}
        content = r.content_json or {}
        for d in DOMAINS:
            if d in scores:
                domain_totals[d] += float(scores[d])
                domain_counts[d] += 1
        for flag in content.get("red_flags", []):
            red_flags_counter[flag] += 1

    average_domain_scores = {
        d: round(domain_totals[d] / domain_counts[d], 1) if domain_counts[d] else 0.0
        for d in DOMAINS
    }
    top_red_flags = [{"label": k, "count": v} for k, v in red_flags_counter.most_common(10)]

    sector_rows = db.execute(
        select(Client.sector, func.count(Client.id)).group_by(Client.sector).order_by(func.count(Client.id).desc())
    ).all()
    sector_distribution = [{"sector": s or "Unspecified", "count": n} for s, n in sector_rows]

    total_completed = (
        db.scalar(
            select(func.count())
            .select_from(DiagnosticSession)
            .where(DiagnosticSession.status == SessionStatus.completed)
        )
        or 0
    )
    total_in_progress = (
        db.scalar(
            select(func.count())
            .select_from(DiagnosticSession)
            .where(DiagnosticSession.status == SessionStatus.in_progress)
        )
        or 0
    )
    total_sessions = (
        db.scalar(select(func.count()).select_from(DiagnosticSession)) or 0
    )
    completion_rate = round(total_completed / total_sessions * 100, 1) if total_sessions else 0.0

    return {
        "average_domain_scores": average_domain_scores,
        "top_red_flags": top_red_flags,
        "sector_distribution": sector_distribution,
        "completion_rate": completion_rate,
        "total_completed": total_completed,
        "total_in_progress": total_in_progress,
    }


# ───────────────────── client-side helpers ─────────────────────

def get_client_for_user(db: Session, user: User) -> Client | None:
    return db.scalar(
        select(Client)
        .options(
            selectinload(Client.diagnostic_sessions).selectinload(DiagnosticSession.reports),
            selectinload(Client.diagnostic_sessions).selectinload(DiagnosticSession.ratings),
        )
        .where(Client.user_id == user.id)
    )


def client_sessions(client: Client) -> list[dict]:
    return [
        _session_summary(s)
        for s in sorted(client.diagnostic_sessions, key=lambda s: s.started_at, reverse=True)
    ]


def shared_reports_for_client(client: Client) -> list[dict]:
    out: list[dict] = []
    for s in sorted(client.diagnostic_sessions, key=lambda s: s.started_at, reverse=True):
        for r in s.reports:
            if r.is_shared:
                out.append(_report_payload(r, session_id=s.id))
    return out


def client_transcript(
    db: Session, *, client: Client, session_id: uuid.UUID
) -> dict | None:
    session = db.scalar(
        select(DiagnosticSession)
        .options(
            selectinload(DiagnosticSession.messages),
            selectinload(DiagnosticSession.reports),
            selectinload(DiagnosticSession.ratings),
        )
        .where(DiagnosticSession.id == session_id, DiagnosticSession.client_id == client.id)
    )
    if session is None:
        return None
    messages = sorted(session.messages, key=lambda m: m.created_at)
    rating = session.ratings[0] if session.ratings else None
    has_shared_report = any(r.is_shared for r in session.reports)
    return {
        "session_id": session.id,
        "status": session.status.value,
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "messages": messages,
        "rating": rating,
        "has_shared_report": has_shared_report,
    }
