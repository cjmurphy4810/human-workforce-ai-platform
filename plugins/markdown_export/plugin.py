"""Markdown Export plugin — reference implementation.

Subscribes to AfterBrief and writes a human-readable executive summary as
``output_dir/YYYY-MM-DD/intelligence_summary.md``.

Demonstrates how to:
- Render a report dict to a custom format.
- Use ``context.config`` to make output configurable.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.events.types import Event, LifecycleEvent

logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    metadata = PluginMetadata(
        name="markdown_export",
        version="1.0.0",
        description="Exports an intelligence summary to a Markdown file after each pipeline run",
        author="Human Workforce AI Team",
        plugin_type="export",
    )

    def __init__(self) -> None:
        self._output_dir = Path("data/exports/markdown_export")
        self._max_items = 10

    async def startup(self, context: PluginContext) -> None:
        self._output_dir = Path(
            context.config.get("output_dir", "data/exports/markdown_export")
        )
        self._max_items = int(context.config.get("max_items", 10))
        context.event_bus.subscribe(LifecycleEvent.AFTER_BRIEF, self._on_after_brief)
        logger.info("Markdown Export plugin started (output_dir=%s)", self._output_dir)

    async def shutdown(self) -> None:
        logger.info("Markdown Export plugin shut down")

    async def _on_after_brief(self, event: Event) -> None:
        report_dict = event.data.get("report_dict")
        if not report_dict:
            logger.warning("AfterBrief event missing 'report_dict' — skipping export")
            return

        dated_dir = self._output_dir / datetime.now(UTC).strftime("%Y-%m-%d")
        dated_dir.mkdir(parents=True, exist_ok=True)

        out_path = dated_dir / "intelligence_summary.md"
        out_path.write_text(
            self._render(report_dict, self._max_items), encoding="utf-8"
        )
        logger.info("Markdown Export wrote %s", out_path)

    @staticmethod
    def _render(report: dict[str, Any], max_items: int) -> str:
        summary = report.get("summary", {})
        lines = [
            "# Executive Intelligence Summary",
            "",
            f"**Generated:** {report.get('generated_at', 'unknown')}",
            f"**Period:** {report.get('period_days', 30)} days",
            "",
            "## Key Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Articles Analyzed | {summary.get('total_articles_analyzed', 0):,} |",
            f"| Opportunities | {summary.get('opportunities_detected', 0)} "
            f"({summary.get('high_priority_opportunities', 0)} high priority) |",
            f"| Trends | {summary.get('trends_identified', 0)} "
            f"({summary.get('emerging_trends', 0)} emerging) |",
            f"| Actions Required | {summary.get('executive_actions_required', 0)} |",
            f"| Top Consulting Value | {summary.get('top_consulting_value', 'N/A')} |",
            "",
        ]

        opps = report.get("opportunities", [])[:max_items]
        if opps:
            lines += ["## Opportunities", ""]
            for opp in opps:
                priority = opp.get("priority", "low")
                badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                lines.append(
                    f"- {badge} **{opp.get('title', '')}** "
                    f"[{opp.get('type', '').replace('_', ' ').title()}] — "
                    f"{priority.title()} priority"
                )
            lines.append("")

        trends = report.get("trends", [])[:max_items]
        if trends:
            lines += ["## Trends", ""]
            for trend in trends:
                velocity = trend.get("velocity", 0.0)
                lines.append(
                    f"- **{trend.get('topic', '')}** "
                    f"({trend.get('type', '').replace('_', ' ').title()}) "
                    f"velocity: {velocity:+.2f}"
                )
            lines.append("")

        return "\n".join(lines)
