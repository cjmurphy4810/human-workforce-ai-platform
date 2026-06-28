"""Intelligence Engine plugin.

Bridges the Executive Intelligence Engine (intelligence-engine/) into the plugin
system.  Subscribes to AfterResearch so the platform can notify it when fresh
article data is available.  The actual pipeline run is still triggered via
POST /intelligence/run; this plugin provides discovery metadata and event
integration so future automation (e.g. auto-run after each research cycle)
can be wired without modifying core platform code.
"""

from __future__ import annotations

import logging

from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.events.types import Event, LifecycleEvent

logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    metadata = PluginMetadata(
        name="intelligence_engine",
        version="1.0.0",
        description=(
            "Executive Intelligence Engine — opportunities, trends, "
            "impact analysis, and recommendations"
        ),
        author="Human Workforce AI Team",
        plugin_type="analytics",
    )

    def __init__(self) -> None:
        self._lookback_days: int = 30

    async def startup(self, context: PluginContext) -> None:
        self._lookback_days = int(context.config.get("lookback_days", 30))
        context.event_bus.subscribe(LifecycleEvent.AFTER_RESEARCH, self._on_after_research)
        context.event_bus.subscribe(LifecycleEvent.AFTER_BRIEF, self._on_after_brief)
        logger.info(
            "Intelligence Engine plugin started (lookback_days=%d)", self._lookback_days
        )

    async def shutdown(self) -> None:
        logger.info("Intelligence Engine plugin shut down")

    async def _on_after_research(self, event: Event) -> None:
        article_count = event.data.get("article_count", 0)
        logger.info(
            "AfterResearch: %d articles available. "
            "Call POST /intelligence/run to regenerate the intelligence report.",
            article_count,
        )

    async def _on_after_brief(self, event: Event) -> None:
        opp_count = event.data.get("opportunities_detected", 0)
        trend_count = event.data.get("trends_identified", 0)
        logger.info(
            "AfterBrief: intelligence report ready — %d opportunities, %d trends",
            opp_count,
            trend_count,
        )
