from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.contact_submission import ContactSubmission
from app.schemas.contact import ContactSubmissionCreate, ContactSubmissionRead

router = APIRouter(prefix="/api", tags=["contact"])


@router.post(
    "/contact",
    response_model=ContactSubmissionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_contact_submission(
    payload: ContactSubmissionCreate,
    db: Session = Depends(get_db),
) -> ContactSubmission:
    submission = ContactSubmission(
        name=payload.name.strip(),
        email=payload.email,
        organization=payload.organization.strip() if payload.organization else None,
        subject=payload.subject.strip(),
        message=payload.message.strip(),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission
