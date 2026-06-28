"""Core data models for the Executive Intelligence Engine.

These models are intentionally independent of the Research Plugin's models.
The API layer is responsible for converting between them.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

# ── Enumerations ──────────────────────────────────────────────────────────────


class OpportunityType(StrEnum):
    CONSULTING = "consulting"
    PODCAST = "podcast"
    BOOK = "book"
    COURSE = "course"
    EXECUTIVE_BRIEFING = "executive_briefing"
    LINKEDIN_CAMPAIGN = "linkedin_campaign"


class TrendType(StrEnum):
    EMERGING = "emerging"
    GROWING = "growing"
    DECLINING = "declining"
    REPEATED = "repeated"
    INDUSTRY_PATTERN = "industry_pattern"
    VENDOR_ACTIVITY = "vendor_activity"
    ENTERPRISE_RISK = "enterprise_risk"


class RecommendationAction(StrEnum):
    PODCAST = "podcast"
    NEWSLETTER = "newsletter"
    CONSULTING_ARTICLE = "consulting_article"
    YOUTUBE_VIDEO = "youtube_video"
    EXECUTIVE_PRESENTATION = "executive_presentation"
    IGNORE = "ignore"


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Article input (decoupled from Research Plugin) ────────────────────────────


@dataclass
class ArticleData:
    """Normalized article representation consumed by the Intelligence Engine."""

    title: str
    url: str
    source_name: str
    published_at: datetime
    summary: str
    business_impact: float
    executive_interest: float
    consulting_opportunity: float
    podcast_potential: float
    urgency: float
    overall: float

    @property
    def id(self) -> str:
        return hashlib.md5(self.url.encode()).hexdigest()[:12]  # noqa: S324


# ── Output primitives ─────────────────────────────────────────────────────────


@dataclass
class ArticleRef:
    """Lightweight article reference used inside intelligence outputs."""

    title: str
    url: str
    source: str
    published_at: str  # ISO-8601 string for JSON serialisability
    overall_score: float


@dataclass
class Opportunity:
    id: str
    type: OpportunityType
    title: str
    priority: Priority
    confidence: float
    estimated_business_value: str
    target_audience: str
    recommended_action: str
    supporting_articles: list[ArticleRef]


@dataclass
class Trend:
    id: str
    topic: str
    type: TrendType
    velocity: float  # positive = growing, negative = declining
    recent_count: int
    baseline_count: int
    avg_score: float
    key_sources: list[str]
    sample_titles: list[str]
    first_seen: str   # ISO-8601
    last_seen: str    # ISO-8601


@dataclass
class ExecutiveImpact:
    topic: str
    article_count: int
    business_impact: float
    technology_impact: float
    operational_risk: float
    governance_impact: float
    regulatory_impact: float
    financial_services_relevance: float
    executive_priority: float
    time_sensitivity: float
    top_articles: list[ArticleRef]


@dataclass
class Recommendation:
    id: str
    action: RecommendationAction
    title: str
    reasoning: str
    score: float
    article_count: int
    articles: list[ArticleRef]


# ── Aggregate report ──────────────────────────────────────────────────────────


@dataclass
class IntelligenceSummary:
    total_articles_analyzed: int
    opportunities_detected: int
    high_priority_opportunities: int
    medium_priority_opportunities: int
    low_priority_opportunities: int
    trends_identified: int
    emerging_trends: int
    executive_actions_required: int
    top_consulting_value: str
    analysis_period_days: int


@dataclass
class IntelligenceReport:
    generated_at: datetime
    period_days: int
    summary: IntelligenceSummary
    opportunities: list[Opportunity]
    trends: list[Trend]
    impact_analysis: list[ExecutiveImpact]
    recommendations: list[Recommendation]

    # Convenience views consumed directly by API endpoints
    @property
    def consulting_opportunities(self) -> list[Opportunity]:
        return [o for o in self.opportunities if o.type == OpportunityType.CONSULTING]

    @property
    def podcast_opportunities(self) -> list[Opportunity]:
        return [o for o in self.opportunities if o.type == OpportunityType.PODCAST]
