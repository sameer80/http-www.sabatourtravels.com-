from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.models import CrawlStatus, Severity, TaskStatus


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str = ""
    organization: str = ""


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    organization: str

    model_config = {"from_attributes": True}


class WebsiteCreate(BaseModel):
    name: str
    domain: str
    base_url: str
    country: str = "IN"
    city: str = ""
    language: str = "en"


class WebsiteOut(BaseModel):
    id: int
    name: str
    domain: str
    base_url: str
    country: str
    city: str
    language: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PageOut(BaseModel):
    id: int
    url: str
    path: str
    title: str | None
    meta_description: str | None
    h1: str | None
    word_count: int
    status_code: int
    internal_links_in: int
    internal_links_out: int
    is_orphan: bool
    images_missing_alt: int

    model_config = {"from_attributes": True}


class CrawlIssueOut(BaseModel):
    id: int
    issue_type: str
    severity: Severity
    message: str
    evidence: dict | None
    page_url: str | None = None

    model_config = {"from_attributes": True}


class CrawlRunOut(BaseModel):
    id: int
    status: CrawlStatus
    pages_crawled: int
    issues_found: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None

    model_config = {"from_attributes": True}


class KeywordCreate(BaseModel):
    query: str
    target_page_id: int | None = None
    country: str = "IN"
    city: str = ""
    language: str = "en"
    device: str = "desktop"
    position: float | None = None


class KeywordOut(BaseModel):
    id: int
    query: str
    country: str
    city: str
    language: str
    device: str
    target_page_id: int | None
    latest_position: float | None = None
    position_change: str | None = None

    model_config = {"from_attributes": True}


class RankHistoryOut(BaseModel):
    id: int
    position: float | None
    recorded_at: datetime

    model_config = {"from_attributes": True}


class CompetitorCreate(BaseModel):
    domain: str
    name: str = ""


class CompetitorOut(BaseModel):
    id: int
    domain: str
    name: str

    model_config = {"from_attributes": True}


class BacklinkOut(BaseModel):
    id: int
    source_url: str
    source_domain: str
    target_url: str
    anchor_text: str | None
    is_dofollow: bool
    is_new: bool
    is_lost: bool

    model_config = {"from_attributes": True}


class OpportunityOut(BaseModel):
    id: int
    title: str
    opportunity_type: str
    score: float
    signals: dict | None
    evidence: str | None
    page_id: int | None
    keyword_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    page_path: str = ""
    reason: str | None = None
    owner: str = "SEO"
    priority: Severity = Severity.MEDIUM
    page_id: int | None = None
    opportunity_id: int | None = None


class TaskUpdate(BaseModel):
    status: TaskStatus | None = None
    owner: str | None = None
    priority: Severity | None = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    page_path: str
    reason: str | None
    owner: str
    priority: Severity
    status: TaskStatus
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    message: str
    conversation_id: int | None = None


class ChatMessageOut(BaseModel):
    role: str
    content: str
    evidence: dict | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: ChatMessageOut
    tasks_created: list[TaskOut] = []


class DashboardOverview(BaseModel):
    website: WebsiteOut
    total_pages: int
    total_issues: int
    issues_by_severity: dict[str, int]
    total_keywords: int
    keywords_top_10: int
    keywords_opportunity_zone: int
    pending_tasks: int
    top_opportunities: list[OpportunityOut]
    recent_alerts: list[dict[str, Any]]


class SerpAnalysisRequest(BaseModel):
    keyword: str
    page_id: int | None = None


class SerpAnalysisOut(BaseModel):
    keyword: str
    user_page: dict[str, Any] | None
    competitors: list[dict[str, Any]]
    content_gaps: list[str]
    recommendations: list[str]


class InternalLinkRecommendation(BaseModel):
    source_page: str
    target_page: str
    anchor_text: str
    reason: str


class GscMetricCreate(BaseModel):
    query: str
    page_url: str = ""
    clicks: int = 0
    impressions: int = 0
    ctr: float = 0.0
    average_position: float = 0.0
