"""JSON Export plugin — reference implementation.

Subscribes to AfterBrief and writes selected fields from the intelligence
report to ``output_dir/YYYY-MM-DD/intelligence_export.json``.

Demonstrates how to:
- Accept a list-valued config key (``fields``).
- Produce a compact JSON payload instead of the full report.
- Add plugin-specific metadata (``exported_at``, ``source``) to the output.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.events.types import Event, LifecycleEvent

logger = logging.getLogger(__name__)

_DEFAULT_FIELDS = ("summary", "opportunities", "trends", "recommendations")


class Plugin(PluginBase):
    metadata = PluginMetadata(
        name="json_export",
        version="1.0.0",
        description=(
            "Exports selected intelligence fields to a compact JSON file "
            "after each pipeline run"
        ),
        author="Human Workforce AI Team",
        plugin_type="export",
    )

    def __init__(self) -> None:
        self._output_dir = Path("data/exports/json_export")
        self._fields: tuple[str, ...] = _DEFAULT_FIELDS

    async def startup(self, context: PluginContext) -> None:
        self._output_dir = Path(
            context.config.get("output_dir", "data/exports/json_export")
        )
        configured_fields = context.config.get("fields")
        if isinstance(configured_fields, list):
            self._fields = tuple(configured_fields)
        context.event_bus.subscribe(LifecycleEvent.AFTER_BRIEF, self._on_after_brief)
        logger.info(
            "JSON Export plugin started (output_dir=%s, fields=%s)",
            self._output_dir,
            self._fields,
        )

    async def shutdown(self) -> None:
        logger.info("JSON Export plugin shut down")

    async def _on_after_brief(self, event: Event) -> None:
        report_dict = event.data.get("report_dict")
        if not report_dict:
            logger.warning("AfterBrief event missing 'report_dict' — skipping export")
            return

        dated_dir = self._output_dir / datetime.now(UTC).strftime("%Y-%m-%d")
        dated_dir.mkdir(parents=True, exist_ok=True)

        payload = self._build_payload(report_dict)
        out_path = dated_dir / "intelligence_export.json"
        out_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        logger.info("JSON Export wrote %s", out_path)

    def _build_payload(self, report: dict[str, Any]) -> dict[str, Any]:
        return {
            "exported_at": datetime.now(UTC).isoformat(),
            "source": "json_export_plugin",
            **{k: report[k] for k in self._fields if k in report},
        }
