"""Plugin SDK — public surface for building Human Workforce AI plugins.

Quick start::

    from plugin_sdk import PluginBase, PluginMetadata, PluginContext
    from plugin_sdk import EventBus, Event, LifecycleEvent
    from plugin_sdk import ServiceRegistry, PluginManager
"""

from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.di import ServiceRegistry
from plugin_sdk.events.bus import EventBus
from plugin_sdk.events.types import Event, LifecycleEvent
from plugin_sdk.exceptions import (
    PluginError,
    PluginLoadError,
    PluginMetadataError,
    ServiceNotFoundError,
)
from plugin_sdk.manager import PluginManager

__all__ = [
    # Core
    "PluginBase",
    "PluginContext",
    "PluginMetadata",
    # DI
    "ServiceRegistry",
    # Events
    "EventBus",
    "Event",
    "LifecycleEvent",
    # Management
    "PluginManager",
    # Exceptions
    "PluginError",
    "PluginLoadError",
    "PluginMetadataError",
    "ServiceNotFoundError",
]
