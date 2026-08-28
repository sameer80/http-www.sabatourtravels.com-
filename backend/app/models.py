import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Severity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PLANNED = "planned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OutreachStatus(str, enum.Enum):
    FOUND = "found"
    READY = "ready_to_post"
    POSTED = "posted"
    LIVE = "live"
    REJECTED = "rejected"


class CrawlStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    organization: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    websites: Mapped[list["Website"]] = relationship(back_populates="owner")


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    domain: Mapped[str] = mapped_column(String(255), index=True)
    base_url: Mapped[str] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(100), default="IN")
    city: Mapped[str] = mapped_column(String(100), default="")
    language: Mapped[str] = mapped_column(String(20), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="websites")
    pages: Mapped[list["Page"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    crawl_runs: Mapped[list["CrawlRun"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    keywords: Mapped[list["Keyword"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    competitors: Mapped[list["Competitor"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    tasks: Mapped[list["SeoTask"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    opportunities: Mapped[list["SeoOpportunity"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    conversations: Mapped[list["AiConversation"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    experiments: Mapped[list["SeoExperiment"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="website", cascade="all, delete-orphan")
    link_prospects: Mapped[list["LinkProspect"]] = relationship(back_populates="website", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    url: Mapped[str] = mapped_column(String(1000), index=True)
    path: Mapped[str] = mapped_column(String(500), default="")
    title: Mapped[str | None] = mapped_column(String(500))
    meta_description: Mapped[str | None] = mapped_column(Text)
    h1: Mapped[str | None] = mapped_column(String(500))
    headings: Mapped[dict | None] = mapped_column(JSON)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    canonical: Mapped[str | None] = mapped_column(String(1000))
    robots: Mapped[str | None] = mapped_column(String(255))
    has_schema: Mapped[bool] = mapped_column(Boolean, default=False)
    images_missing_alt: Mapped[int] = mapped_column(Integer, default=0)
    internal_links_out: Mapped[int] = mapped_column(Integer, default=0)
    internal_links_in: Mapped[int] = mapped_column(Integer, default=0)
    is_orphan: Mapped[bool] = mapped_column(Boolean, default=False)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    website: Mapped["Website"] = relationship(back_populates="pages")
    crawl_issues: Mapped[list["CrawlIssue"]] = relationship(back_populates="page", cascade="all, delete-orphan")
    rank_history: Mapped[list["RankHistory"]] = relationship(back_populates="page")
    internal_links_from: Mapped[list["InternalLink"]] = relationship(
        back_populates="source_page", foreign_keys="InternalLink.source_page_id"
    )
    internal_links_to: Mapped[list["InternalLink"]] = relationship(
        back_populates="target_page", foreign_keys="InternalLink.target_page_id"
    )


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    status: Mapped[CrawlStatus] = mapped_column(Enum(CrawlStatus), default=CrawlStatus.PENDING)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0)
    issues_found: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)

    website: Mapped["Website"] = relationship(back_populates="crawl_runs")
    issues: Mapped[list["CrawlIssue"]] = relationship(back_populates="crawl_run", cascade="all, delete-orphan")


class CrawlIssue(Base):
    __tablename__ = "crawl_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    crawl_run_id: Mapped[int] = mapped_column(ForeignKey("crawl_runs.id"), index=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    issue_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[Severity] = mapped_column(Enum(Severity))
    message: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSON)

    crawl_run: Mapped["CrawlRun"] = relationship(back_populates="issues")
    page: Mapped["Page | None"] = relationship(back_populates="crawl_issues")


class Keyword(Base):
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    query: Mapped[str] = mapped_column(String(500), index=True)
    target_page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="IN")
    city: Mapped[str] = mapped_column(String(100), default="")
    language: Mapped[str] = mapped_column(String(20), default="en")
    device: Mapped[str] = mapped_column(String(20), default="desktop")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    website: Mapped["Website"] = relationship(back_populates="keywords")
    target_page: Mapped["Page | None"] = relationship()
    rank_history: Mapped[list["RankHistory"]] = relationship(back_populates="keyword", cascade="all, delete-orphan")
    gsc_metrics: Mapped[list["GscMetric"]] = relationship(back_populates="keyword", cascade="all, delete-orphan")


class RankHistory(Base):
    __tablename__ = "rank_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), index=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    position: Mapped[float | None] = mapped_column(Float)
    search_engine: Mapped[str] = mapped_column(String(50), default="google")
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    keyword: Mapped["Keyword"] = relationship(back_populates="rank_history")
    page: Mapped["Page | None"] = relationship(back_populates="rank_history")


class GscMetric(Base):
    __tablename__ = "gsc_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    page_url: Mapped[str] = mapped_column(String(1000), default="")
    query: Mapped[str] = mapped_column(String(500), default="")
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    ctr: Mapped[float] = mapped_column(Float, default=0.0)
    average_position: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    keyword: Mapped["Keyword | None"] = relationship(back_populates="gsc_metrics")


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    domain: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), default="")

    website: Mapped["Website"] = relationship(back_populates="competitors")
    pages: Mapped[list["CompetitorPage"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")
    backlinks: Mapped[list["Backlink"]] = relationship(back_populates="competitor", cascade="all, delete-orphan")


class CompetitorPage(Base):
    __tablename__ = "competitor_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str | None] = mapped_column(String(500))
    keyword: Mapped[str | None] = mapped_column(String(500))
    position: Mapped[float | None] = mapped_column(Float)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    headings: Mapped[dict | None] = mapped_column(JSON)
    has_faq: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    competitor: Mapped["Competitor"] = relationship(back_populates="pages")


class Backlink(Base):
    __tablename__ = "backlinks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), nullable=True, index=True)
    competitor_id: Mapped[int | None] = mapped_column(ForeignKey("competitors.id"), nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(String(1000))
    source_domain: Mapped[str] = mapped_column(String(255), index=True)
    target_url: Mapped[str] = mapped_column(String(1000))
    anchor_text: Mapped[str | None] = mapped_column(String(500))
    is_dofollow: Mapped[bool] = mapped_column(Boolean, default=True)
    is_new: Mapped[bool] = mapped_column(Boolean, default=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


    competitor: Mapped["Competitor | None"] = relationship(back_populates="backlinks")


class LinkProspect(Base):
    __tablename__ = "link_prospects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    keyword: Mapped[str] = mapped_column(String(500), index=True)
    target_url: Mapped[str] = mapped_column(String(1000))
    prospect_url: Mapped[str] = mapped_column(String(1000))
    prospect_domain: Mapped[str] = mapped_column(String(255), index=True)
    prospect_title: Mapped[str | None] = mapped_column(String(500))
    prospect_type: Mapped[str] = mapped_column(String(100), default="editorial")
    domain_authority: Mapped[float] = mapped_column(Float, default=0.0)
    page_authority: Mapped[float] = mapped_column(Float, default=0.0)
    page_rank: Mapped[float] = mapped_column(Float, default=0.0)
    suggested_anchor: Mapped[str | None] = mapped_column(String(500))
    google_query: Mapped[str | None] = mapped_column(String(500))
    outreach_status: Mapped[OutreachStatus] = mapped_column(Enum(OutreachStatus), default=OutreachStatus.FOUND)
    posted_url: Mapped[str | None] = mapped_column(String(1000))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    website: Mapped["Website"] = relationship(back_populates="link_prospects")


class InternalLink(Base):
    __tablename__ = "internal_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    source_page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    target_page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"))
    anchor_text: Mapped[str | None] = mapped_column(String(500))

    source_page: Mapped["Page"] = relationship(back_populates="internal_links_from", foreign_keys=[source_page_id])
    target_page: Mapped["Page"] = relationship(back_populates="internal_links_to", foreign_keys=[target_page_id])


class SeoOpportunity(Base):
    __tablename__ = "seo_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    opportunity_type: Mapped[str] = mapped_column(String(100))
    score: Mapped[float] = mapped_column(Float, default=0.0)
    signals: Mapped[dict | None] = mapped_column(JSON)
    evidence: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    website: Mapped["Website"] = relationship(back_populates="opportunities")


class SeoTask(Base):
    __tablename__ = "seo_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    page_id: Mapped[int | None] = mapped_column(ForeignKey("pages.id"), nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("seo_opportunities.id"), nullable=True)
    priority: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.MEDIUM)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    page_path: Mapped[str] = mapped_column(String(500), default="")
    reason: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String(100), default="SEO")
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    website: Mapped["Website"] = relationship(back_populates="tasks")


class SeoExperiment(Base):
    __tablename__ = "seo_experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("seo_tasks.id"), nullable=True)
    change_description: Mapped[str] = mapped_column(Text)
    target_page: Mapped[str] = mapped_column(String(500), default="")
    target_keyword: Mapped[str] = mapped_column(String(500), default="")
    expected_impact: Mapped[str | None] = mapped_column(Text)
    observed_result: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    was_successful: Mapped[bool | None] = mapped_column(Boolean)
    implemented_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    website: Mapped["Website"] = relationship(back_populates="experiments")


class AiConversation(Base):
    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(255), default="SEO Chat")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    website: Mapped["Website"] = relationship(back_populates="conversations")
    messages: Mapped[list["AiMessage"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class AiMessage(Base):
    __tablename__ = "ai_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("ai_conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["AiConversation"] = relationship(back_populates="messages")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int] = mapped_column(ForeignKey("websites.id"), index=True)
    alert_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[Severity] = mapped_column(Enum(Severity), default=Severity.MEDIUM)
    title: Mapped[str] = mapped_column(String(500))
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    website: Mapped["Website"] = relationship(back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    website_id: Mapped[int | None] = mapped_column(ForeignKey("websites.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    website: Mapped["Website | None"] = relationship(back_populates="audit_logs")
