from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Article(BaseModel):
    title: str
    url: str
    source_name: str
    source_weight: float = 1.0
    published_at: datetime
    fetched_at: datetime = Field(default_factory=_utcnow)
    summary: str = ""
    content_hash: str = ""


class ArticleScore(BaseModel):
    business_impact: float = Field(default=0.0, ge=0.0, le=1.0)
    executive_interest: float = Field(default=0.0, ge=0.0, le=1.0)
    consulting_opportunity: float = Field(default=0.0, ge=0.0, le=1.0)
    podcast_potential: float = Field(default=0.0, ge=0.0, le=1.0)
    urgency: float = Field(default=0.0, ge=0.0, le=1.0)
    overall: float = Field(default=0.0, ge=0.0, le=1.0)


class ScoredArticle(BaseModel):
    article: Article
    score: ArticleScore
    db_id: int | None = None
