import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_csrf, require_role
from app.db.session import get_db
from app.models.client import Client
from app.models.diagnostic_session import DiagnosticSession
from app.models.rating import Rating
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    ClientOverview,
    ClientProfileUpdate,
    ClientTranscript,
    RateSessionRequest,
    RatingOut,
    ReportPayload,
    SessionSummary,
)
from app.services import dashboard as svc

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
