"""KnowledgePlugin interface — semantic indexing and retrieval."""

from __future__ import annotations

from abc import abstractmethod

from plugin_sdk.base import PluginBase


class KnowledgePlugin(PluginBase):
    """Indexes research content and answers semantic queries.

    Future implementations: NotebookLMPlugin, local vector-store plugin.
    """

    @abstractmethod
    async def index(
        self,
        documents: list[str],
        metadata: list[dict] | None = None,
    ) -> None:
        """Add documents (and optional per-doc metadata) to the knowledge index."""
        ...

    @abstractmethod
    async def search(self, query: str, top_k: int = 5) -> list[str]:
        """Return the ``top_k`` most relevant document excerpts for ``query``."""
        ...
