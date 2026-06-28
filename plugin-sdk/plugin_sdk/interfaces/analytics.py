"""AnalyticsPlugin interface — event tracking and business metrics."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from plugin_sdk.base import PluginBase


class AnalyticsPlugin(PluginBase):
    """Tracks platform events and surfaces aggregated business metrics.

    Built-in implementation: intelligence_engine (opportunities, trends,
    impact analysis).
    """

    @abstractmethod
    async def track_event(self, name: str, data: dict[str, Any]) -> None:
        """Record a named event with an arbitrary data payload."""
        ...

    @abstractmethod
    async def get_metrics(self, window_days: int = 30) -> dict[str, Any]:
        """Return aggregated metrics for the specified trailing window."""
        ...
