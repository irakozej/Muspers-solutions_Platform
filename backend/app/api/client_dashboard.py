import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.deps import get_current_user, require_csrf, require_role
from app.db.session import get_db
from app.models.client import Client
from app.models.diagnostic_session import DiagnosticSession
from app.models.rating import Rating
from app.models.report import Report
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    ClientOverview,
    ClientProfileUpdate,
    ClientTranscript,
    RateSessionRequest,
    RatingOut,
    ReportPayload,
    SessionSummary,
    TeaserSnapshot,
)
from app.models.diagnostic_session import SessionStatus
from app.services import dashboard as svc
from app.services import pdf_report
from app.services.teaser import build_teaser

router = APIRouter(prefix="/api/client", tags=["client-dashboard"])


def _require_client_profile(db: Session, user: User) -> Client:
    client = svc.get_client_for_user(db, user)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No business profile linked to this account yet.",
        )
    return client


@router.get("/me", response_model=ClientOverview)
def my_overview(
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> dict:
    client = svc.get_client_for_user(db, user)
    return {
        "business_name": client.business_name if client else None,
        "sector": client.sector if client else None,
        "full_name": user.full_name,
        "sessions": svc.client_sessions(client) if client else [],
        "shared_reports": svc.shared_reports_for_client(client) if client else [],
    }


@router.get("/sessions", response_model=list[SessionSummary])
def my_sessions(
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> list[dict]:
    client = _require_client_profile(db, user)
    return svc.client_sessions(client)


@router.get("/reports", response_model=list[ReportPayload])
def my_shared_reports(
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> list[dict]:
    client = _require_client_profile(db, user)
    return svc.shared_reports_for_client(client)


def _owned_session(db: Session, client: Client, session_id: uuid.UUID) -> DiagnosticSession:
    """404 when it does not exist, 403 when it belongs to another client."""
    session = db.scalar(
        select(DiagnosticSession)
        .options(selectinload(DiagnosticSession.reports))
        .where(DiagnosticSession.id == session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This session does not belong to your account.",
        )
    return session


@router.get("/sessions/{session_id}/snapshot", response_model=TeaserSnapshot)
def snapshot(
    session_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> dict:
    """The teaser: headline scores and two area names, available the moment
    the interview completes. Everything else waits for Penny to share."""
    client = _require_client_profile(db, user)
    session = _owned_session(db, client, session_id)
    if session.status != SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Your snapshot will be ready when the interview is complete.",
        )
    return build_teaser(session)


@router.get("/reports/{report_id}", response_model=ReportPayload)
def shared_report(
    report_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> dict:
    """One full report. 403 until Penny shares it, and for anyone else's."""
    client = _require_client_profile(db, user)
    report = db.scalar(
        select(Report).options(selectinload(Report.session)).where(Report.id == report_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if not report.session or report.session.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report does not belong to your account.",
        )
    if not report.is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report has not been shared with you yet.",
        )
    return svc._report_payload(report, session_id=report.session_id)


@router.get("/sessions/{session_id}/transcript", response_model=ClientTranscript)
def transcript(
    session_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> dict:
    client = _require_client_profile(db, user)
    data = svc.client_transcript(db, client=client, session_id=session_id)
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return data


@router.post(
    "/sessions/{session_id}/rate",
    response_model=RatingOut,
    status_code=status.HTTP_201_CREATED,
)
def rate_session(
    session_id: uuid.UUID,
    payload: RateSessionRequest,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> Rating:
    client = _require_client_profile(db, user)
    session = db.scalar(
        select(DiagnosticSession).where(
            DiagnosticSession.id == session_id, DiagnosticSession.client_id == client.id
        )
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    existing = db.scalar(select(Rating).where(Rating.session_id == session_id))
    if existing is not None:
        existing.score = payload.score
        existing.feedback = payload.feedback
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    rating = Rating(
        session_id=session_id,
        score=payload.score,
        feedback=payload.feedback,
    )
    db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating


@router.get("/reports/{report_id}/report.pdf")
def download_shared_report_pdf(
    report_id: uuid.UUID,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
) -> Response:
    client = _require_client_profile(db, user)

    report = db.scalar(
        select(Report)
        .options(selectinload(Report.session).selectinload(DiagnosticSession.client))
        .where(Report.id == report_id)
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Security checks: report must be shared AND belong to this client.
    if not report.is_shared:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report has not been shared with you yet.",
        )
    if not report.session or report.session.client_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This report does not belong to your account.",
        )

    detail = svc.client_detail(db, client.id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    # Build the report dict in the same shape as latest_report.
    report_dict = svc._report_payload(report, session_id=report.session_id)
    pdf_bytes, filename = pdf_report.render_report_pdf(client=detail, report=report_dict)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.patch("/profile", response_model=ClientOverview)
def update_business_profile(
    payload: ClientProfileUpdate,
    user: User = Depends(require_role(UserRole.client)),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> dict:
    client = _require_client_profile(db, user)
    if payload.business_name is not None:
        client.business_name = payload.business_name.strip()
    if payload.sector is not None:
        client.sector = payload.sector.strip() or None
    if payload.location is not None:
        client.location = payload.location.strip() or None
    if payload.employee_count is not None:
        client.employee_count = payload.employee_count
    db.add(client)
    db.commit()
    db.refresh(client)
    return {
        "business_name": client.business_name,
        "sector": client.sector,
        "full_name": user.full_name,
        "sessions": svc.client_sessions(client),
        "shared_reports": svc.shared_reports_for_client(client),
    }
