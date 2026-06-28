"""Core plugin abstractions: PluginMetadata, PluginContext, and PluginBase."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from plugin_sdk.di import ServiceRegistry
    from plugin_sdk.events.bus import EventBus


@dataclass
class PluginMetadata:
    """Static descriptor declared at class level on every plugin."""

    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True


class PluginContext:
    """Injected into every plugin at startup.

    Gives plugins access to:
    - ``services``  — the ServiceRegistry (DI container)
    - ``event_bus`` — subscribe/emit lifecycle and domain events
    - ``config``    — dict of plugin-specific config from plugin.toml [config]
                       merged with any global override from plugins.toml
    """

    def __init__(
        self,
        services: ServiceRegistry,
        event_bus: EventBus,
        config: dict[str, Any],
    ) -> None:
        self.services = services
        self.event_bus = event_bus
        self.config = config


class PluginBase(ABC):
    """Abstract base class that every plugin must subclass.

    Subclass requirements:
    - Define a class-level ``metadata: PluginMetadata`` attribute.
    - Implement ``startup(context)`` — subscribe to events, initialise state.
    - Implement ``shutdown()``       — release resources, unsubscribe if needed.

    The concrete class inside each plugin package must be named ``Plugin``.
    """

    metadata: PluginMetadata

    @abstractmethod
    async def startup(self, context: PluginContext) -> None:
        """Called once at application startup after the plugin is loaded."""
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Called once at application shutdown in reverse load order."""
        ...

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.metadata.name!r} v{self.metadata.version}>"
