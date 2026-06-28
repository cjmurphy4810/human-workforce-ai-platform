"""Intelligence Engine API router.

Endpoints:
  POST /intelligence/run    — run the full intelligence pipeline
  GET  /intelligence        — latest full report
  GET  /opportunities       — all opportunities (filterable by type)
  GET  /recommendations     — per-article recommendations
  GET  /trends              — trend analysis grouped by type
  GET  /consulting          — consulting pipeline
  GET  /podcasts            — podcast opportunities
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.dependencies import get_agent1_dir, get_config, get_event_bus, get_repo
from api.models.intelligence_responses import (
    ConsultingPipelineResponse,
    IntelligenceReportResponse,
    IntelligenceRunResponse,
    OpportunityListResponse,
    RecommendationListResponse,
    TrendAnalysisResponse,
)

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])
logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_intelligence_dir(agent1_dir: Path) -> Path:
    """Intelligence outputs live alongside the research data."""
    intel_dir = agent1_dir.parent / "intelligence-engine" / "data" / "output"
    return intel_dir


def _find_latest_output(output_root: Path, filename: str) -> Path | None:
    if not output_root.exists():
        return None
    for dated_dir in sorted(output_root.glob("????-??-??"), reverse=True):
        candidate = dated_dir / filename
        if candidate.exists():
            return candidate
    return None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _no_report_error() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail="No intelligence report found. Run POST /intelligence/run to generate one.",
    )


# ── Pipeline trigger ──────────────────────────────────────────────────────────


@router.post(
    "/run",
    response_model=IntelligenceRunResponse,
    summary="Run the Intelligence Engine",
    description=(
        "Fetches all stored articles from the research database, runs all analyzers "
        "(opportunity detection, trend analysis, impact analysis, recommendations), "
        "and writes output files to intelligence-engine/data/output/YYYY-MM-DD/."
    ),
)
async def run_intelligence(
    config: Any = Depends(get_config),
    repo: Any = Depends(get_repo),
    agent1_dir: Path = Depends(get_agent1_dir),
    event_bus: Any = Depends(get_event_bus),
    lookback_days: Annotated[int, Query(ge=7, le=365, description="Analysis window in days")] = 30,
) -> IntelligenceRunResponse:
    from intelligence.models.intelligence import ArticleData  # noqa: PLC0415
    from intelligence.output.writer import write_outputs  # noqa: PLC0415
    from intelligence.pipeline.intelligence_pipeline import (  # noqa: PLC0415
        PipelineConfig,
        run_intelligence_pipeline,
    )
    from plugin_sdk.events.types import Event, LifecycleEvent  # noqa: PLC0415

    t0 = time.monotonic()

    if event_bus is not None:
        await event_bus.emit(
            Event(type=LifecycleEvent.BEFORE_BRIEF, source="intelligence")
        )

    # Fetch all articles from the research repository
    items, total = await repo.get_articles_filtered(
        date=None, source=None, min_score=0.0,
        dimension=None, limit=5000, offset=0,
    )

    # Convert to ArticleData (intelligence engine's own model)
    articles: list[ArticleData] = [
        ArticleData(
            title=sa.article.title,
            url=sa.article.url,
            source_name=sa.article.source_name,
            published_at=sa.article.published_at,
            summary=sa.article.summary or "",
            business_impact=sa.score.business_impact,
            executive_interest=sa.score.executive_interest,
            consulting_opportunity=sa.score.consulting_opportunity,
            podcast_potential=sa.score.podcast_potential,
            urgency=sa.score.urgency,
            overall=sa.score.overall,
        )
        for sa in items
    ]

    cfg = PipelineConfig(lookback_days=lookback_days)
    report = run_intelligence_pipeline(articles, config=cfg)

    output_dir = _load_intelligence_dir(agent1_dir)
    written = write_outputs(report, output_dir)

    elapsed = round(time.monotonic() - t0, 2)

    if event_bus is not None:
        from dataclasses import asdict  # noqa: PLC0415
        await event_bus.emit(
            Event(
                type=LifecycleEvent.AFTER_BRIEF,
                data={
                    "report_dict": asdict(report),
                    "output_dir": str(output_dir),
                    "articles_analyzed": len(articles),
                    "opportunities_detected": len(report.opportunities),
                    "trends_identified": len(report.trends),
                },
                source="intelligence",
            )
        )

    return IntelligenceRunResponse(
        status="completed",
        generated_at=report.generated_at.isoformat(),
        articles_analyzed=len(articles),
        opportunities_detected=len(report.opportunities),
        trends_identified=len(report.trends),
        recommendations_generated=len(report.recommendations),
        output_files=[str(p) for p in written.values()],
        duration_seconds=elapsed,
    )


# ── Read endpoints ────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=IntelligenceReportResponse,
    summary="Latest intelligence report",
    description="Returns the most recently generated full intelligence report.",
)
async def get_intelligence(
    agent1_dir: Path = Depends(get_agent1_dir),
) -> IntelligenceReportResponse:
    output_root = _load_intelligence_dir(agent1_dir)
    path = _find_latest_output(output_root, "executive_intelligence.json")
    if path is None:
        raise _no_report_error()
    data = _load_json(path)
    return IntelligenceReportResponse(**data)


@router.get(
    "/opportunities",
    response_model=OpportunityListResponse,
    summary="All detected opportunities",
    description="Returns all opportunities. Filter by type: consulting, podcast, book, course, executive_briefing, linkedin_campaign.",
)
async def get_opportunities(
    agent1_dir: Path = Depends(get_agent1_dir),
    type: Annotated[str | None, Query(description="Filter by opportunity type")] = None,
) -> OpportunityListResponse:
    output_root = _load_intelligence_dir(agent1_dir)
    path = _find_latest_output(output_root, "executive_intelligence.json")
    if path is None:
        raise _no_report_error()
    data = _load_json(path)
    opps = data.get("opportunities", [])
    if type:
        opps = [o for o in opps if o.get("type") == type]
    return OpportunityListResponse(
        generated_at=data.get("generated_at", ""),
        total=len(opps),
        opportunities=opps,
    )


@router.get(
    "/recommendations",
    response_model=RecommendationListResponse,
    summary="Per-article recommendations",
    description="Returns recommendations for each article. Filter by action: podcast, newsletter, consulting_article, youtube_video, executive_presentation.",
)
async def get_recommendations(
    agent1_dir: Path = Depends(get_agent1_dir),
    action: Annotated[str | None, Query(description="Filter by recommended action")] = None,
) -> RecommendationListResponse:
    output_root = _load_intelligence_dir(agent1_dir)
    path = _find_latest_output(output_root, "executive_recommendations.json")
    if path is None:
        raise _no_report_error()
    data = _load_json(path)
    recs = data.get("recommendations", [])
    if action:
        recs = [r for r in recs if r.get("action") == action]
    return RecommendationListResponse(
        generated_at=data.get("generated_at", ""),
        total=len(recs),
        recommendations=recs,
    )


@router.get(
    "/trends",
    response_model=TrendAnalysisResponse,
    summary="Trend analysis",
    description="Returns trend analysis grouped by type: emerging, growing, declining, repeated, industry_pattern, vendor_activity, enterprise_risk.",
)
async def get_trends(
    agent1_dir: Path = Depends(get_agent1_dir),
) -> TrendAnalysisResponse:
    output_root = _load_intelligence_dir(agent1_dir)
    path = _find_latest_output(output_root, "trend_analysis.json")
    if path is None:
        raise _no_report_error()
    data = _load_json(path)
    return TrendAnalysisResponse(**data)


@router.get(
    "/consulting",
    response_model=ConsultingPipelineResponse,
    summary="Consulting opportunity pipeline",
    description="Returns prioritized consulting opportunities with business value estimates.",
)
async def get_consulting(
    agent1_dir: Path = Depends(get_agent1_dir),
) -> ConsultingPipelineResponse:
    output_root = _load_intelligence_dir(agent1_dir)
    path = _find_latest_output(output_root, "consulting_pipeline.json")
    if path is None:
        raise _no_report_error()
    data = _load_json(path)
    return ConsultingPipelineResponse(**data)


@router.get(
    "/podcasts",
    response_model=OpportunityListResponse,
    summary="Podcast opportunities",
    description="Returns podcast opportunities filtered from the intelligence report.",
)
async def get_podcasts(
    agent1_dir: Path = Depends(get_agent1_dir),
) -> OpportunityListResponse:
    output_root = _load_intelligence_dir(agent1_dir)
    path = _find_latest_output(output_root, "executive_intelligence.json")
    if path is None:
        raise _no_report_error()
    data = _load_json(path)
    podcasts = [o for o in data.get("opportunities", []) if o.get("type") == "podcast"]
    return OpportunityListResponse(
        generated_at=data.get("generated_at", ""),
        total=len(podcasts),
        opportunities=podcasts,
    )
