"""VideoPlugin interface — AI-generated video from research content."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from plugin_sdk.base import PluginBase


class VideoPlugin(PluginBase):
    """Generates video content from research data and briefings.

    Future implementations: AIVideoPlugin, ElevenLabsPlugin.
    """

    @abstractmethod
    async def generate_script(self, topic: str, content: str, **kwargs: Any) -> str:
        """Generate a narration script for the given topic and supporting content."""
        ...

    @abstractmethod
    async def render_video(self, script: str, **kwargs: Any) -> bytes:
        """Render a video from the narration script. Returns raw video bytes."""
        ...
