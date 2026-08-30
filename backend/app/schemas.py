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
    positioning: str = ""
    seo_focus: str = ""
    sitemap_url: str | None = None


class WebsiteOut(BaseModel):
    id: int
    name: str
    domain: str
    base_url: str
    country: str
    city: str
    language: str
    positioning: str = ""
    seo_focus: str = ""
    sitemap_url: str | None = None
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
    previous_position: float | None = None
    position_change: float | None = None
    position_trend: str | None = None
    priority_zone: str | None = None
    search_volume: int | None = None
    keyword_difficulty: float | None = None

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
    seo_score: float
    total_pages: int
    total_issues: int
    issues_by_severity: dict[str, int]
    total_keywords: int
    keywords_top_3: int
    keywords_top_10: int
    keywords_top_20: int
    keywords_high_opportunity: int
    keywords_top_10_legacy: int
    keywords_opportunity_zone: int
    pending_tasks: int
    top_opportunities: list[OpportunityOut]
    recent_alerts: list[dict[str, Any]]


class PortfolioOverview(BaseModel):
    organization: str
    websites: list[WebsiteOut]
    totals: dict[str, Any]
    site_summaries: list[dict[str, Any]]


class AiRecommendationOut(BaseModel):
    id: int
    title: str
    opportunity_type: str
    score: float
    evidence: str | None
    signals: dict | None
    priority: str
    suggested_owner: str
    validation_method: str
    status: str = "open"


class DailyReportOut(BaseModel):
    generated_at: str
    website: dict[str, Any]
    summary: dict[str, Any]
    keyword_movements: list[dict[str, Any]]
    top_recommendations: list[dict[str, Any]]
    workflow_note: str


class ApiSyncLogOut(BaseModel):
    id: int
    provider: str
    sync_type: str
    status: str
    records_synced: int
    message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


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


class LinkProspectSearchRequest(BaseModel):
    keyword: str
    target_url: str
    min_da: float = 30
    min_pa: float = 25
    anchor_text: str | None = None


class LinkProspectOut(BaseModel):
    id: int
    keyword: str
    target_url: str
    prospect_url: str
    prospect_domain: str
    prospect_title: str | None
    prospect_type: str
    domain_authority: float
    page_authority: float
    page_rank: float
    suggested_anchor: str | None
    google_query: str | None
    outreach_status: str
    posted_url: str | None
    notes: str | None
    created_at: datetime
    posted_at: datetime | None

    model_config = {"from_attributes": True}


class LinkProspectPostRequest(BaseModel):
    posted_url: str | None = None
    notes: str | None = None
    outreach_status: str = "posted"


class LinkProspectSearchOut(BaseModel):
    keyword: str
    target_url: str
    found: int
    prospects: list[LinkProspectOut]
    submission_plan: dict[str, str]
