from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from models.article import Article, ArticleScore, ScoredArticle
from storage.orm import ArticleORM

logger = logging.getLogger(__name__)

_DIMENSION_COLUMNS: dict[str, object] = {
    "business_impact": ArticleORM.score_business_impact,
    "executive_interest": ArticleORM.score_executive_interest,
    "consulting_opportunity": ArticleORM.score_consulting_opportunity,
    "podcast_potential": ArticleORM.score_podcast_potential,
    "urgency": ArticleORM.score_urgency,
}


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

    # ── pipeline methods ────────────────────────────────────────────────────

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

    # ── API query methods ────────────────────────────────────────────────────

    async def count_all(self) -> int:
        async with self._factory() as session:
            result = await session.execute(select(func.count()).select_from(ArticleORM))
            return result.scalar_one() or 0

    async def count_since(self, days: int) -> int:
        cutoff = _utcnow() - timedelta(days=days)
        async with self._factory() as session:
            result = await session.execute(
                select(func.count())
                .select_from(ArticleORM)
                .where(ArticleORM.fetched_at >= cutoff)
            )
            return result.scalar_one() or 0

    async def get_latest_fetch_time(self) -> Optional[datetime]:
        async with self._factory() as session:
            result = await session.execute(
                select(func.max(ArticleORM.fetched_at))
            )
            return result.scalar_one_or_none()

    async def get_articles_filtered(
        self,
        *,
        date: Optional[str] = None,
        source: Optional[str] = None,
        min_score: float = 0.0,
        dimension: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ScoredArticle], int]:
        """Returns (items, total_count) with optional filters and pagination."""
        async with self._factory() as session:
            stmt = select(ArticleORM)
            count_stmt = select(func.count()).select_from(ArticleORM)

            if date:
                try:
                    day = datetime.strptime(date, "%Y-%m-%d")
                    day_start = day.replace(tzinfo=timezone.utc)
                    day_end = day_start + timedelta(days=1)
                    stmt = stmt.where(
                        ArticleORM.published_at >= day_start,
                        ArticleORM.published_at < day_end,
                    )
                    count_stmt = count_stmt.where(
                        ArticleORM.published_at >= day_start,
                        ArticleORM.published_at < day_end,
                    )
                except ValueError:
                    pass  # invalid date — ignore filter

            if source:
                like = f"%{source}%"
                stmt = stmt.where(ArticleORM.source_name.ilike(like))
                count_stmt = count_stmt.where(ArticleORM.source_name.ilike(like))

            if min_score > 0:
                stmt = stmt.where(ArticleORM.score_overall >= min_score)
                count_stmt = count_stmt.where(ArticleORM.score_overall >= min_score)

            # Sort by requested dimension or fall back to overall
            if dimension and dimension in _DIMENSION_COLUMNS:
                order_col = _DIMENSION_COLUMNS[dimension]
                stmt = stmt.order_by(order_col.desc().nullslast())  # type: ignore[union-attr]
            else:
                stmt = stmt.order_by(ArticleORM.score_overall.desc().nullslast())

            total_result = await session.execute(count_stmt)
            total = total_result.scalar_one() or 0

            stmt = stmt.limit(limit).offset(offset)
            result = await session.execute(stmt)
            items = [_orm_to_scored(row) for row in result.scalars().all()]

        return items, total

    async def get_source_stats(self, since_days: int = 30) -> list[dict]:
        """Returns per-source aggregates: name, count, avg_overall, latest_published."""
        cutoff = _utcnow() - timedelta(days=since_days)
        async with self._factory() as session:
            result = await session.execute(
                select(
                    ArticleORM.source_name,
                    func.count().label("article_count"),
                    func.avg(ArticleORM.score_overall).label("avg_score"),
                    func.max(ArticleORM.published_at).label("latest_published"),
                )
                .where(ArticleORM.fetched_at >= cutoff)
                .group_by(ArticleORM.source_name)
                .order_by(func.count().desc())
            )
            return [
                {
                    "source_name": row.source_name,
                    "article_count": row.article_count,
                    "avg_score": round(float(row.avg_score or 0.0), 4),
                    "latest_published": row.latest_published,
                }
                for row in result.all()
            ]

    async def get_dimension_averages(self, since_days: int = 30) -> dict[str, dict]:
        """Returns per-dimension aggregates and the top article for each."""
        cutoff = _utcnow() - timedelta(days=since_days)
        async with self._factory() as session:
            agg = await session.execute(
                select(
                    func.count().label("n"),
                    func.avg(ArticleORM.score_business_impact).label("bi"),
                    func.avg(ArticleORM.score_executive_interest).label("ei"),
                    func.avg(ArticleORM.score_consulting_opportunity).label("co"),
                    func.avg(ArticleORM.score_podcast_potential).label("pp"),
                    func.avg(ArticleORM.score_urgency).label("ur"),
                )
                .where(ArticleORM.fetched_at >= cutoff)
            )
            row = agg.one()
            n = row.n or 0

            dimensions: dict[str, dict] = {
                "business_impact": {"label": "Business Impact", "avg": round(float(row.bi or 0), 4), "article_count": n},
                "executive_interest": {"label": "Executive Interest", "avg": round(float(row.ei or 0), 4), "article_count": n},
                "consulting_opportunity": {"label": "Consulting Opportunity", "avg": round(float(row.co or 0), 4), "article_count": n},
                "podcast_potential": {"label": "Podcast Potential", "avg": round(float(row.pp or 0), 4), "article_count": n},
                "urgency": {"label": "Urgency", "avg": round(float(row.ur or 0), 4), "article_count": n},
            }

            # Top article per dimension
            for dim_key, col in _DIMENSION_COLUMNS.items():
                top = await session.execute(
                    select(ArticleORM)
                    .where(ArticleORM.fetched_at >= cutoff)
                    .order_by(col.desc().nullslast())  # type: ignore[union-attr]
                    .limit(1)
                )
                top_row = top.scalar_one_or_none()
                dimensions[dim_key]["top_article"] = (
                    _orm_to_scored(top_row) if top_row else None
                )

        return dimensions
