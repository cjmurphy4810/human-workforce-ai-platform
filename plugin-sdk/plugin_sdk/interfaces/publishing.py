"""PublishingPlugin interface — distribute content to external platforms."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from plugin_sdk.base import PluginBase


class PublishingPlugin(PluginBase):
    """Publishes generated content to an external platform.

    Future implementations: LinkedInPlugin, YouTubePlugin, GitHubPlugin.
    """

    @abstractmethod
    async def publish(self, content: str, metadata: dict[str, Any]) -> str:
        """Publish content. Returns a URL or handle identifying the published item."""
        ...

    @abstractmethod
    async def unpublish(self, handle: str) -> None:
        """Remove a previously published item identified by ``handle``."""
        ...
