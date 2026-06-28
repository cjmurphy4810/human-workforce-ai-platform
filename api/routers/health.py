from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_agent1_dir, get_config, get_repo
from api.models.responses import HealthResponse

router = APIRouter(tags=["System"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
    description="Returns API status, database connectivity, and configuration summary.",
)
async def health(
    request: Request,
    config=Depends(get_config),
    agent1_dir: Path = Depends(get_agent1_dir),
    repo=Depends(get_repo),
) -> HealthResponse:
    db_ok = True
    try:
        await repo.count_all()
    except Exception:
        db_ok = False

    status = "healthy" if db_ok else "degraded"

    return HealthResponse(
        status=status,
        timestamp=datetime.now(UTC),
        database="connected" if db_ok else "disconnected",
        sources_configured=len(config.sources),
    )
