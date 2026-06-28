"""Pydantic response models for the Intelligence Engine API endpoints."""

from __future__ import annotations

from pydantic import BaseModel

# ── Shared primitives ─────────────────────────────────────────────────────────


class ArticleRefResponse(BaseModel):
    title: str
    url: str
    source: str
    published_at: str
    overall_score: float


# ── Opportunities ─────────────────────────────────────────────────────────────


class OpportunityResponse(BaseModel):
    id: str
    type: str
    title: str
    priority: str
    confidence: float
    estimated_business_value: str
    target_audience: str
    recommended_action: str
    supporting_articles: list[ArticleRefResponse]


class OpportunityListResponse(BaseModel):
    generated_at: str
    total: int
    opportunities: list[OpportunityResponse]


# ── Trends ────────────────────────────────────────────────────────────────────


class TrendResponse(BaseModel):
    id: str
    topic: str
    type: str
    velocity: float
    recent_count: int
    baseline_count: int
    avg_score: float
    key_sources: list[str]
    sample_titles: list[str]
    first_seen: str
    last_seen: str


class TrendAnalysisResponse(BaseModel):
    generated_at: str
    analysis_window_days: int
    recent_window_days: int
    total_trends: int
    trends: dict[str, list[TrendResponse]]


# ── Recommendations ───────────────────────────────────────────────────────────


class RecommendationResponse(BaseModel):
    id: str
    action: str
    title: str
    reasoning: str
    score: float
    article_count: int
    articles: list[ArticleRefResponse]


class RecommendationListResponse(BaseModel):
    generated_at: str
    total: int
    recommendations: list[RecommendationResponse]


# ── Impact Analysis ───────────────────────────────────────────────────────────


class ExecutiveImpactResponse(BaseModel):
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
    top_articles: list[ArticleRefResponse]


# ── Consulting Pipeline ───────────────────────────────────────────────────────


class ConsultingPipelineResponse(BaseModel):
    generated_at: str
    total: int
    pipeline: list[OpportunityResponse]


# ── Intelligence Summary ──────────────────────────────────────────────────────


class IntelligenceSummaryResponse(BaseModel):
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


# ── Full Report ───────────────────────────────────────────────────────────────


class IntelligenceReportResponse(BaseModel):
    generated_at: str
    period_days: int
    summary: IntelligenceSummaryResponse
    opportunities: list[OpportunityResponse]
    trends: list[TrendResponse]
    impact_analysis: list[ExecutiveImpactResponse]
    recommendations: list[RecommendationResponse]


# ── Run response ──────────────────────────────────────────────────────────────


class IntelligenceRunResponse(BaseModel):
    status: str
    generated_at: str
    articles_analyzed: int
    opportunities_detected: int
    trends_identified: int
    recommendations_generated: int
    output_files: list[str]
    duration_seconds: float
