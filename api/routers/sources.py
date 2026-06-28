from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.dependencies import get_config, get_repo
from api.models.responses import SourceListResponse, SourceResponse

router = APIRouter(tags=["Sources"])


@router.get(
    "/sources",
    response_model=SourceListResponse,
    summary="Configured sources with DB stats",
    description=(
        "Returns all configured RSS sources merged with database statistics "
        "(article count, average score, latest article date)."
    ),
)
async def list_sources(
    config: Any = Depends(get_config),
    repo: Any = Depends(get_repo),
) -> SourceListResponse:
    db_stats = await repo.get_source_stats(since_days=90)
    stats_by_name = {row["source_name"]: row for row in db_stats}

    items = [
        SourceResponse(
            name=src.name,
            url=src.url,
            weight=src.weight,
            article_count=stats_by_name.get(src.name, {}).get("article_count", 0),
            avg_score=stats_by_name.get(src.name, {}).get("avg_score", 0.0),
            latest_article_date=stats_by_name.get(src.name, {}).get("latest_published"),
        )
        for src in config.sources
    ]

    return SourceListResponse(items=items, total=len(items))
