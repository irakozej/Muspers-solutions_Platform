import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_csrf, require_role
from app.db.session import get_db
from app.models.advisor_note import AdvisorNote
from app.models.report import Report
from app.models.user import User, UserRole
from app.schemas.dashboard import (
    AdvisorNoteCreate,
    AdvisorNoteOut,
    AdvisorStats,
    AnalyticsResponse,
    ClientDetail,
    ClientSummary,
    ShareUpdate,
)
from app.services import dashboard as svc

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


@router.get("/stats", response_model=AdvisorStats)
def stats(
    _: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
) -> dict:
    return svc.collect_advisor_stats(db)


@router.get("/clients", response_model=list[ClientSummary])
def clients(
    search: str | None = None,
    sector: str | None = None,
    _: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
) -> list[dict]:
    return svc.list_clients(db, search=search, sector=sector)


@router.get("/clients/{client_id}", response_model=ClientDetail)
def client_detail(
    client_id: uuid.UUID,
    _: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
) -> dict:
    detail = svc.client_detail(db, client_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return detail


@router.post(
    "/clients/{client_id}/notes",
    response_model=AdvisorNoteOut,
    status_code=status.HTTP_201_CREATED,
)
def add_note(
    client_id: uuid.UUID,
    payload: AdvisorNoteCreate,
    advisor: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> AdvisorNote:
    detail = svc.client_detail(db, client_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    note = AdvisorNote(
        client_id=client_id,
        advisor_id=advisor.id,
        content=payload.content.strip(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.patch("/reports/{report_id}/share")
def toggle_share(
    report_id: uuid.UUID,
    payload: ShareUpdate,
    _: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
    _csrf: None = Depends(require_csrf),
) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    report.is_shared = payload.is_shared
    db.add(report)
    db.commit()
    return {"id": str(report.id), "is_shared": report.is_shared}


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    _: User = Depends(require_role(UserRole.advisor)),
    db: Session = Depends(get_db),
) -> dict:
    return svc.collect_analytics(db)
