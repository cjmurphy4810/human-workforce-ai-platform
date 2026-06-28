"""AIProviderPlugin interface — text generation and embedding."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any

from plugin_sdk.base import PluginBase


class AIProviderPlugin(PluginBase):
    """Wraps an AI model API (Claude, OpenAI, Gemini, local models, etc.).

    Future implementations: ClaudePlugin, OpenAIPlugin, HermesPlugin.
    """

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Generate a text completion for the given prompt."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return a vector embedding for the given text."""
        ...
