"""ResearchPlugin interface — fetch and score content from external sources."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from plugin_sdk.base import PluginBase


class ResearchPlugin(PluginBase):
    """Fetches articles from external sources and scores them for relevance.

    Built-in implementation: agent1-research (RSS + AI scoring pipeline).
    """

    @abstractmethod
    async def fetch_articles(
        self,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch articles matching ``query``. Returns a list of article dicts."""
        ...

    @abstractmethod
    async def score_articles(
        self,
        articles: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Score articles for business relevance.

        Implementations should add score fields to each dict and return them
        sorted by overall score descending.
        """
        ...
