"""Local File Export plugin — reference implementation.

Subscribes to AfterBrief and writes the complete intelligence report as a
single JSON file under ``output_dir/YYYY-MM-DD/intelligence_export.json``.

This plugin demonstrates the minimal pattern for an export plugin:
1. Read config in startup().
2. Subscribe to AfterBrief.
3. Write output in the event handler.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.events.types import Event, LifecycleEvent

logger = logging.getLogger(__name__)


class Plugin(PluginBase):
    metadata = PluginMetadata(
        name="local_file_export",
        version="1.0.0",
        description="Exports the full intelligence report to a local file after each pipeline run",
        author="Human Workforce AI Team",
        plugin_type="export",
    )

    def __init__(self) -> None:
        self._output_dir = Path("data/exports/local_file_export")

    async def startup(self, context: PluginContext) -> None:
        output_dir = context.config.get("output_dir", "data/exports/local_file_export")
        self._output_dir = Path(output_dir)
        context.event_bus.subscribe(LifecycleEvent.AFTER_BRIEF, self._on_after_brief)
        logger.info("Local File Export plugin started (output_dir=%s)", self._output_dir)

    async def shutdown(self) -> None:
        logger.info("Local File Export plugin shut down")

    async def _on_after_brief(self, event: Event) -> None:
        report_dict = event.data.get("report_dict")
        if not report_dict:
            logger.warning("AfterBrief event missing 'report_dict' — skipping export")
            return

        dated_dir = self._output_dir / datetime.now(UTC).strftime("%Y-%m-%d")
        dated_dir.mkdir(parents=True, exist_ok=True)

        out_path = dated_dir / "intelligence_export.json"
        out_path.write_text(
            json.dumps(report_dict, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info("Local File Export wrote %s", out_path)
