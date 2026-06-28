from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repo
from api.models.responses import ArticleListResponse, ArticleResponse, ArticleScoreResponse

router = APIRouter(tags=["Articles"])

_VALID_DIMENSIONS = {
    "business_impact",
    "executive_interest",
    "consulting_opportunity",
    "podcast_potential",
    "urgency",
}


def _to_article_response(sa: Any) -> ArticleResponse:
    a = sa.article
    s = sa.score
    return ArticleResponse(
        title=a.title,
        url=a.url,
        source_name=a.source_name,
        published_at=a.published_at,
        fetched_at=a.fetched_at,
        summary=a.summary,
        score=ArticleScoreResponse(
            business_impact=s.business_impact,
            executive_interest=s.executive_interest,
            consulting_opportunity=s.consulting_opportunity,
            podcast_potential=s.podcast_potential,
            urgency=s.urgency,
            overall=s.overall,
        ),
    )


@router.get(
    "/articles",
    response_model=ArticleListResponse,
    summary="List stored articles",
    description=(
        "Returns paginated articles from the database. "
        "Filter by `date` (YYYY-MM-DD), `source` (partial name), "
        "`min_score` (0.0–1.0), or `topic` (scoring dimension to sort by)."
    ),
)
async def list_articles(
    repo: Annotated[Any, Depends(get_repo)],
    date: Annotated[
        str | None,
        Query(
            description="Filter by published date (YYYY-MM-DD)",
            example="2026-06-28",
        ),
    ] = None,
    source: Annotated[
        str | None,
        Query(
            description="Filter by source name (partial match)",
            example="TechCrunch",
        ),
    ] = None,
    min_score: Annotated[
        float,
        Query(
            ge=0.0,
            le=1.0,
            description="Minimum overall score",
        ),
    ] = 0.0,
    topic: Annotated[
        str | None,
        Query(
            description="Sort by scoring dimension: business_impact, executive_interest, "
            "consulting_opportunity, podcast_potential, urgency",
        ),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200, description="Max results")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
) -> ArticleListResponse:
    dimension = topic if topic in _VALID_DIMENSIONS else None

    items, total = await repo.get_articles_filtered(
        date=date,
        source=source,
        min_score=min_score,
        dimension=dimension,
        limit=limit,
        offset=offset,
    )

    return ArticleListResponse(
        items=[_to_article_response(sa) for sa in items],
        total=total,
        limit=limit,
        offset=offset,
    )
