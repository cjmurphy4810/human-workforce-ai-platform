from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pipeline.orchestrator import orchestrate_run

from api.auth import verify_api_key
from api.dependencies import get_agent1_dir, get_config, get_repo
from api.models.responses import RunResponse, SourceError

router = APIRouter(tags=["Pipeline"])
logger = logging.getLogger(__name__)


@router.post(
    "/run",
    response_model=RunResponse,
    summary="Run the research pipeline",
    description=(
        "Fetches all configured RSS sources, deduplicates and scores articles, "
        "persists them to the database, and writes a fresh Executive Brief. "
        "Runs synchronously — expect 5–30 seconds depending on network conditions."
    ),
    dependencies=[Depends(verify_api_key)],
)
async def run_pipeline(
    config=Depends(get_config),
    repo=Depends(get_repo),
    agent1_dir: Path = Depends(get_agent1_dir),
) -> RunResponse:

    output_root = agent1_dir / config.output.directory

    try:
        result = await orchestrate_run(config, repo, output_root)
    except Exception as exc:
        logger.exception("pipeline run failed")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {exc}") from exc

    return RunResponse(
        status="completed",
        timestamp=result.timestamp,
        articles_fetched=result.articles_fetched,
        articles_new=result.articles_new,
        articles_saved=result.articles_saved,
        sources_attempted=result.sources_attempted,
        sources_succeeded=result.sources_succeeded,
        source_errors=[SourceError(source=name, error=err) for name, err in result.source_errors],
        save_errors=result.save_errors,
        brief_path=result.brief_path,
        duration_seconds=result.duration_seconds,
    )
