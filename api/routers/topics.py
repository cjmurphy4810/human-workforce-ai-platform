from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from api.dependencies import get_repo
from api.models.responses import (
    ArticleResponse,
    ArticleScoreResponse,
    TopicListResponse,
    TopicResponse,
)

router = APIRouter(tags=["Topics"])

_DIMENSION_LABELS = {
    "business_impact": "Business Impact",
    "executive_interest": "Executive Interest",
    "consulting_opportunity": "Consulting Opportunity",
    "podcast_potential": "Podcast Potential",
    "urgency": "Urgency",
}


def _to_article_response(sa: Any) -> ArticleResponse | None:
    if sa is None:
        return None
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
    "/topics",
    response_model=TopicListResponse,
    summary="Topic (scoring dimension) summaries",
    description=(
        "Returns aggregated statistics for each of the 5 scoring dimensions "
        "— Business Impact, Executive Interest, Consulting Opportunity, "
        "Podcast Potential, and Urgency — with the top article for each."
    ),
)
async def list_topics(
    repo: Annotated[Any, Depends(get_repo)],
    since_days: Annotated[int, Query(ge=1, le=365, description="Lookback window in days")] = 30,
) -> TopicListResponse:
    dim_data = await repo.get_dimension_averages(since_days=since_days)

    items = [
        TopicResponse(
            id=dim_id,
            label=_DIMENSION_LABELS.get(dim_id, dim_id),
            article_count=data["article_count"],
            avg_score=data["avg"],
            top_article=_to_article_response(data.get("top_article")),
        )
        for dim_id, data in dim_data.items()
    ]

    # Sort by avg_score descending so highest-signal dimension appears first
    items.sort(key=lambda t: t.avg_score, reverse=True)

    return TopicListResponse(items=items, since_days=since_days)
