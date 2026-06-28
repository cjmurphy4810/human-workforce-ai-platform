"""Pydantic response models for the Human Workforce AI API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Health ──────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    version: str = "1.0.0"
    timestamp: datetime
    database: Literal["connected", "disconnected"]
    sources_configured: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2026-06-28T14:00:00Z",
                "database": "connected",
                "sources_configured": 9,
            }
        }
    }


# ── Stats ────────────────────────────────────────────────────────────────────


class StatsResponse(BaseModel):
    total_articles: int
    articles_last_7_days: int
    articles_last_30_days: int
    sources_configured: int
    last_fetch: datetime | None


# ── Brief ────────────────────────────────────────────────────────────────────


class BriefResponse(BaseModel):
    date: str = Field(description="YYYY-MM-DD of the brief")
    path: str = Field(description="Absolute path to the brief file")
    content: str = Field(description="Full Markdown content")
    word_count: int
    character_count: int


# ── Pipeline run ─────────────────────────────────────────────────────────────


class SourceError(BaseModel):
    source: str
    error: str


class RunResponse(BaseModel):
    status: Literal["completed", "failed"]
    timestamp: datetime
    articles_fetched: int
    articles_new: int
    articles_saved: int
    sources_attempted: int
    sources_succeeded: int
    source_errors: list[SourceError]
    save_errors: list[str]
    brief_path: str
    duration_seconds: float


# ── Articles ─────────────────────────────────────────────────────────────────


class ArticleScoreResponse(BaseModel):
    business_impact: float
    executive_interest: float
    consulting_opportunity: float
    podcast_potential: float
    urgency: float
    overall: float


class ArticleResponse(BaseModel):
    title: str
    url: str
    source_name: str
    published_at: datetime
    fetched_at: datetime
    summary: str
    score: ArticleScoreResponse


class ArticleListResponse(BaseModel):
    items: list[ArticleResponse]
    total: int
    limit: int
    offset: int


# ── Topics ───────────────────────────────────────────────────────────────────


class TopicResponse(BaseModel):
    id: str = Field(description="Scoring dimension key")
    label: str
    article_count: int
    avg_score: float
    top_article: ArticleResponse | None


class TopicListResponse(BaseModel):
    items: list[TopicResponse]
    since_days: int


# ── Sources ──────────────────────────────────────────────────────────────────


class SourceResponse(BaseModel):
    name: str
    url: str
    weight: float
    article_count: int = 0
    avg_score: float = 0.0
    latest_article_date: datetime | None = None


class SourceListResponse(BaseModel):
    items: list[SourceResponse]
    total: int
