from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies import get_config, get_repo
from api.models.responses import StatsResponse

router = APIRouter(tags=["Stats"])


@router.get(
    "/stats",
    response_model=StatsResponse,
    summary="Database statistics",
    description="Returns total article counts and recent activity metrics.",
)
async def stats(
    config=Depends(get_config),
    repo=Depends(get_repo),
) -> StatsResponse:
    total, last_7, last_30, last_fetch = await _gather_stats(repo)
    return StatsResponse(
        total_articles=total,
        articles_last_7_days=last_7,
        articles_last_30_days=last_30,
        sources_configured=len(config.sources),
        last_fetch=last_fetch,
    )


async def _gather_stats(repo) -> tuple:  # type: ignore[type-arg]
    total = await repo.count_all()
    last_7 = await repo.count_since(7)
    last_30 = await repo.count_since(30)
    last_fetch = await repo.get_latest_fetch_time()
    return total, last_7, last_30, last_fetch
