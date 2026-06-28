"""Intelligence Pipeline — orchestrates all analyzers into a single IntelligenceReport.

This is the single entry point for consumers (CLI, API, tests).
It is intentionally thin: it delegates all analysis to the individual modules
and assembles their outputs into the final report.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from intelligence.analyzers.impact_analyzer import analyze_executive_impact
from intelligence.analyzers.opportunity_detector import detect_all_opportunities
from intelligence.analyzers.trend_detector import detect_trends
from intelligence.config.defaults import LOOKBACK_DAYS, RECENT_WINDOW_DAYS
from intelligence.engines.recommendation_engine import generate_recommendations
from intelligence.engines.scoring_engine import ScoringEngine
from intelligence.models.intelligence import (
    ArticleData,
    IntelligenceReport,
    IntelligenceSummary,
    Priority,
)

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    lookback_days: int = LOOKBACK_DAYS
    recent_window_days: int = RECENT_WINDOW_DAYS
    scoring_strategy: str | None = None  # None = use engine default


def run_intelligence_pipeline(
    articles: list[ArticleData],
    config: PipelineConfig | None = None,
    engine: ScoringEngine | None = None,
) -> IntelligenceReport:
    """Run the full intelligence pipeline and return a complete IntelligenceReport.

    Args:
        articles:  Normalized article data from the Research Plugin.
        config:    Pipeline configuration (defaults to module-level defaults).
        engine:    Scoring engine instance.  Pass a custom engine to inject
                   alternative scoring strategies (e.g. Claude-backed scorer).

    Returns:
        IntelligenceReport with opportunities, trends, impact analysis,
        and per-article recommendations.
    """
    cfg = config or PipelineConfig()
    engine = engine or ScoringEngine()

    t0 = time.monotonic()
    logger.info(
        "intelligence pipeline starting: %d articles, lookback=%d days",
        len(articles),
        cfg.lookback_days,
    )

    # ── 1. Opportunity detection ──────────────────────────────────────────────
    opportunities = detect_all_opportunities(articles, engine, cfg.lookback_days)
    logger.info("opportunities detected: %d", len(opportunities))

    # ── 2. Trend detection ────────────────────────────────────────────────────
    trends = detect_trends(articles, cfg.lookback_days, cfg.recent_window_days)
    logger.info("trends detected: %d", len(trends))

    # ── 3. Executive impact analysis ──────────────────────────────────────────
    impact_analysis = analyze_executive_impact(articles, cfg.lookback_days)
    logger.info("impact topics analyzed: %d", len(impact_analysis))

    # ── 4. Recommendations ────────────────────────────────────────────────────
    recommendations = generate_recommendations(articles, cfg.lookback_days)
    logger.info("recommendations generated: %d", len(recommendations))

    # ── 5. Assemble summary ───────────────────────────────────────────────────
    high_opps = [o for o in opportunities if o.priority == Priority.HIGH]
    medium_opps = [o for o in opportunities if o.priority == Priority.MEDIUM]
    low_opps = [o for o in opportunities if o.priority == Priority.LOW]

    from intelligence.models.intelligence import TrendType
    emerging = [t for t in trends if t.type == TrendType.EMERGING]

    exec_actions = len(high_opps) + len([r for r in recommendations if r.score >= 0.70])

    top_consulting = next(
        (o.estimated_business_value for o in opportunities
         if o.type.value == "consulting" and o.priority == Priority.HIGH),
        "No high-priority consulting opportunities in this period",
    )

    summary = IntelligenceSummary(
        total_articles_analyzed=len(articles),
        opportunities_detected=len(opportunities),
        high_priority_opportunities=len(high_opps),
        medium_priority_opportunities=len(medium_opps),
        low_priority_opportunities=len(low_opps),
        trends_identified=len(trends),
        emerging_trends=len(emerging),
        executive_actions_required=min(exec_actions, 20),
        top_consulting_value=top_consulting,
        analysis_period_days=cfg.lookback_days,
    )

    elapsed = round(time.monotonic() - t0, 2)
    logger.info("intelligence pipeline complete in %.2fs", elapsed)

    return IntelligenceReport(
        generated_at=datetime.now(UTC),
        period_days=cfg.lookback_days,
        summary=summary,
        opportunities=opportunities,
        trends=trends,
        impact_analysis=impact_analysis,
        recommendations=recommendations,
    )
