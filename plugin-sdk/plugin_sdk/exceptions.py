"""Plugin system exceptions."""

from __future__ import annotations


class PluginError(Exception):
    """Base exception for all plugin system errors."""


class PluginLoadError(PluginError):
    """Raised when a plugin cannot be discovered, imported, or instantiated."""


class PluginMetadataError(PluginError):
    """Raised when plugin.toml is missing required [plugin] fields."""


class ServiceNotFoundError(PluginError):
    """Raised when a plugin requests a service that is not registered."""
