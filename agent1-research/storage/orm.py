from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    __allow_unmapped__ = True


class ArticleORM(Base):
    __tablename__ = "articles"
    __table_args__ = (
        Index("ix_articles_published_at", "published_at"),
        Index("ix_articles_source_name", "source_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    source_name = Column(String(200), nullable=False)
    source_weight = Column(Float, default=1.0)
    published_at = Column(DateTime(timezone=True), nullable=False)
    fetched_at = Column(DateTime(timezone=True), default=_utcnow)
    summary = Column(Text, default="")
    content_hash = Column(String(64), nullable=False, unique=True, index=True)

    score_business_impact = Column(Float, nullable=True)
    score_executive_interest = Column(Float, nullable=True)
    score_consulting_opportunity = Column(Float, nullable=True)
    score_podcast_potential = Column(Float, nullable=True)
    score_urgency = Column(Float, nullable=True)
    score_overall = Column(Float, nullable=True)
