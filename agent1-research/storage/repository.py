from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.article import Article, ArticleScore, ScoredArticle
from storage.orm import ArticleORM

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _orm_to_scored(row: ArticleORM) -> ScoredArticle:
    article = Article(
        title=row.title,
        url=row.url,
        source_name=row.source_name,
        source_weight=float(row.source_weight or 1.0),
        published_at=row.published_at,
        fetched_at=row.fetched_at,
        summary=row.summary or "",
        content_hash=row.content_hash,
    )
    score = ArticleScore(
        business_impact=float(row.score_business_impact or 0.0),
        executive_interest=float(row.score_executive_interest or 0.0),
        consulting_opportunity=float(row.score_consulting_opportunity or 0.0),
        podcast_potential=float(row.score_podcast_potential or 0.0),
        urgency=float(row.score_urgency or 0.0),
        overall=float(row.score_overall or 0.0),
    )
    return ScoredArticle(article=article, score=score, db_id=row.id)


class ArticleRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = session_factory

    async def get_existing_hashes(self, since_days: int = 30) -> set[str]:
        cutoff = _utcnow() - timedelta(days=since_days)
        async with self._factory() as session:
            result = await session.execute(
                select(ArticleORM.content_hash).where(ArticleORM.fetched_at >= cutoff)
            )
            return {row[0] for row in result.all()}

    async def save_article(self, scored: ScoredArticle) -> int:
        a = scored.article
        s = scored.score
        row = ArticleORM(
            title=a.title,
            url=a.url,
            source_name=a.source_name,
            source_weight=a.source_weight,
            published_at=a.published_at,
            fetched_at=a.fetched_at,
            summary=a.summary,
            content_hash=a.content_hash,
            score_business_impact=s.business_impact,
            score_executive_interest=s.executive_interest,
            score_consulting_opportunity=s.consulting_opportunity,
            score_podcast_potential=s.podcast_potential,
            score_urgency=s.urgency,
            score_overall=s.overall,
        )
        async with self._factory() as session:
            session.add(row)
            await session.flush()
            await session.commit()
            return int(row.id)

    async def get_recent_articles(
        self, since_days: int, min_score: float = 0.0
    ) -> list[ScoredArticle]:
        cutoff = _utcnow() - timedelta(days=since_days)
        async with self._factory() as session:
            stmt = (
                select(ArticleORM)
                .where(ArticleORM.published_at >= cutoff)
                .order_by(ArticleORM.score_overall.desc().nullslast())
            )
            if min_score > 0:
                stmt = stmt.where(ArticleORM.score_overall >= min_score)
            result = await session.execute(stmt)
            return [_orm_to_scored(row) for row in result.scalars().all()]
