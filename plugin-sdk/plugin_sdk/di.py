"""Lightweight dependency injection container for the plugin system."""

from __future__ import annotations

from typing import Any

from plugin_sdk.exceptions import ServiceNotFoundError


class ServiceRegistry:
    """Holds named services that are injected into plugins at startup.

    Plugins call ``context.services.require("name")`` to receive only the
    services they declare they need.  The platform registers core services
    (repo, config, etc.) once at startup; plugins may register additional
    services for other plugins to consume.
    """

    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        """Register (or replace) a named service."""
        self._services[name] = service

    def get(self, name: str) -> Any | None:
        """Return the service or ``None`` if not registered."""
        return self._services.get(name)

    def require(self, name: str) -> Any:
        """Return the service or raise ``ServiceNotFoundError``."""
        if name not in self._services:
            raise ServiceNotFoundError(
                f"Service '{name}' is not registered. "
                f"Available: {self.list_services()}"
            )
        return self._services[name]

    def has(self, name: str) -> bool:
        return name in self._services

    def list_services(self) -> list[str]:
        return sorted(self._services.keys())
