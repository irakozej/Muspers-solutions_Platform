import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ───────────────────── small reusable pieces ─────────────────────

class StatTile(BaseModel):
    label: str
    value: float | int | str
    detail: str | None = None


class ActivityEvent(BaseModel):
    kind: str  # "client_registered" | "diagnostic_completed" | "rating_received"
    title: str
    description: str | None = None
    at: datetime
    client_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    role: str
    content: str
    created_at: datetime


class RatingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    score: int
    feedback: str | None
    created_at: datetime


class AdvisorNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    content: str
    created_at: datetime


class AdvisorNoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


# ───────────────────── report shape ─────────────────────

class DomainScores(BaseModel):
    strategy: float
    customers: float
    money: float
    operations: float
    talent: float


class HeadlineScores(BaseModel):
    grow_overall: float
    grow_band: str
    finance_readiness: float
    finance_band: str


class ReportPayload(BaseModel):
    """Materialised report. Two shapes share this payload:

    - "hatana" (Phase 6 mock model): headline + domains + red_flags etc.
    - "root_cause" (MusperSolutions' real framework, Phase 4 Part 2): scan_results,
      diagnosis, service_pathway, engagement. The headline block still carries
      the scan aggregate so list views work identically for both.
    """
    id: uuid.UUID
    session_id: uuid.UUID
    report_type: str = "hatana"
    headline: HeadlineScores
    domains: DomainScores
    summary: str | None = None
    red_flags: list[str] = []
    priority_actions: list[dict[str, Any]] = []
    suggested_topics: list[str] = []
    is_shared: bool
    created_at: datetime
    # Root-cause sections (None/absent on legacy reports)
    scan_results: dict[str, Any] | None = None
    # Money Habits (empty / None on reports from before the stage existed)
    finance_results: dict[str, Any] | None = None
    financial_health_pct: int | None = None
    snapshot: dict[str, Any] | None = None
    diagnosis: dict[str, Any] | None = None
    service_pathway: list[dict[str, Any]] | None = None
    engagement: dict[str, Any] | None = None


# ───────────────────── advisor responses ─────────────────────

class AdvisorStats(BaseModel):
    total_clients: int
    active_sessions_this_week: int
    completed_sessions: int
    average_grow_overall: float
    reports_pending_share: int
    recent_activity: list[ActivityEvent]


class ClientSummary(BaseModel):
    """Row in the advisor's clients table."""
    id: uuid.UUID
    business_name: str
    sector: str | None
    location: str | None
    business_size: str | None
    employee_count: int | None
    overall_score: float | None
    band: str | None
    finance_readiness: float | None
    last_activity: datetime | None
    session_status: str | None
    is_shared: bool
    has_report: bool


class SessionSummary(BaseModel):
    id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    overall_score: float | None
    band: str | None
    is_shared: bool
    rating_score: int | None


class ClientDetail(BaseModel):
    id: uuid.UUID
    business_name: str
    sector: str | None
    location: str | None
    business_size: str | None
    employee_count: int | None
    founded_year: int | None
    revenue_band: str | None
    revenue_trend: list[dict[str, Any]] | None
    contact_email: str | None
    contact_name: str | None
    created_at: datetime
    sessions: list[SessionSummary]
    latest_report: ReportPayload | None
    transcript: list[ChatMessageOut]
    rating: RatingOut | None
    notes: list[AdvisorNoteOut]


class AnalyticsResponse(BaseModel):
    average_domain_scores: dict[str, float]
    top_red_flags: list[dict[str, Any]]  # [{label, count}]
    sector_distribution: list[dict[str, Any]]  # [{sector, count}]
    completion_rate: float
    total_completed: int
    total_in_progress: int


class ShareUpdate(BaseModel):
    is_shared: bool


# ───────────────────── client responses ─────────────────────

class ClientOverview(BaseModel):
    business_name: str | None
    sector: str | None
    full_name: str | None
    sessions: list[SessionSummary]
    shared_reports: list[ReportPayload]


class ClientTranscript(BaseModel):
    session_id: uuid.UUID
    status: str
    started_at: datetime
    completed_at: datetime | None
    messages: list[ChatMessageOut]
    rating: RatingOut | None
    has_shared_report: bool


class RateSessionRequest(BaseModel):
    score: int = Field(ge=1, le=5)
    feedback: str | None = Field(default=None, max_length=2000)


class ClientProfileUpdate(BaseModel):
    business_name: str | None = Field(default=None, min_length=1, max_length=255)
    sector: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    employee_count: int | None = Field(default=None, ge=0)
