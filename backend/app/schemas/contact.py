import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactSubmissionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    organization: str | None = Field(default=None, max_length=200)
    subject: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=5000)


class ContactSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: EmailStr
    organization: str | None
    subject: str
    message: str
    created_at: datetime
