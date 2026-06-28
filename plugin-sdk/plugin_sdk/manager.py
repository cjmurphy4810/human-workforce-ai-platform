"""PluginManager — discovers, loads, and orchestrates plugin lifecycle."""

from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Any

from plugin_sdk.base import PluginBase, PluginContext
from plugin_sdk.config import load_global_config, load_plugin_toml
from plugin_sdk.di import ServiceRegistry
from plugin_sdk.events.bus import EventBus
from plugin_sdk.events.types import Event, LifecycleEvent
from plugin_sdk.exceptions import PluginLoadError, PluginMetadataError

logger = logging.getLogger(__name__)

_REQUIRED_META = frozenset({"name", "version", "description", "author", "type"})


class PluginManager:
    """Manages the full lifecycle of all plugins.

    Typical usage::

        manager = PluginManager(plugins_dir, services, event_bus)
        manager.load_all()          # discover + load all enabled plugins
        await manager.startup()     # call startup() on each + emit STARTUP event
        ...
        await manager.shutdown()    # emit SHUTDOWN + call shutdown() in reverse
    """

    def __init__(
        self,
        plugins_dir: Path,
        services: ServiceRegistry,
        event_bus: EventBus,
    ) -> None:
        self._plugins_dir = plugins_dir
        self._services = services
        self._event_bus = event_bus
        self._plugins: dict[str, PluginBase] = {}
        self._global_config: dict[str, Any] = load_global_config(plugins_dir)

        # Ensure ``import plugins.<name>.plugin`` resolves from the repo root.
        repo_root = str(plugins_dir.parent)
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

    # ── Discovery ──────────────────────────────────────────────────────────────

    def discover(self) -> list[str]:
        """Return sorted names of all plugin directories that contain plugin.toml."""
        if not self._plugins_dir.exists():
            return []
        return sorted(
            d.name
            for d in self._plugins_dir.iterdir()
            if d.is_dir()
            and not d.name.startswith("_")
            and (d / "plugin.toml").exists()
        )

    # ── Loading ────────────────────────────────────────────────────────────────

    def load(self, plugin_name: str) -> None:
        """Load a single plugin by directory name.

        Raises:
            PluginLoadError: directory missing, import failed, or no Plugin class.
            PluginMetadataError: plugin.toml [plugin] missing required fields.
        """
        plugin_dir = self._plugins_dir / plugin_name
        if not plugin_dir.exists():
            raise PluginLoadError(f"Plugin directory not found: {plugin_dir}")

        toml = load_plugin_toml(plugin_dir)
        meta = toml.get("plugin", {})
        global_override = self._global_config.get(plugin_name, {})

        enabled = global_override.get("enabled", meta.get("enabled", True))
        if not enabled:
            logger.info("Plugin '%s' is disabled — skipping", plugin_name)
            return

        self._validate_metadata(plugin_name, meta)

        try:
            module = importlib.import_module(f"plugins.{plugin_name}.plugin")
        except ImportError as exc:
            raise PluginLoadError(
                f"Cannot import plugins.{plugin_name}.plugin: {exc}"
            ) from exc

        plugin_class = getattr(module, "Plugin", None)
        if not (
            isinstance(plugin_class, type) and issubclass(plugin_class, PluginBase)
        ):
            raise PluginLoadError(
                f"plugins.{plugin_name}.plugin must define a 'Plugin' class "
                f"that subclasses PluginBase"
            )

        self._plugins[plugin_name] = plugin_class()
        logger.info("Loaded plugin: %s v%s", meta["name"], meta["version"])

    def load_all(self) -> None:
        """Discover and load every enabled plugin; log failures and continue."""
        for name in self.discover():
            try:
                self.load(name)
            except (PluginLoadError, PluginMetadataError):
                logger.exception("Failed to load plugin '%s'", name)

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def startup(self) -> None:
        """Call startup() on all loaded plugins, then emit STARTUP."""
        for name, plugin in self._plugins.items():
            plugin_dir = self._plugins_dir / name
            toml = load_plugin_toml(plugin_dir)

            plugin_config: dict[str, Any] = dict(toml.get("config", {}))
            global_plugin = self._global_config.get(name, {})
            if isinstance(global_plugin.get("config"), dict):
                plugin_config.update(global_plugin["config"])

            context = PluginContext(
                services=self._services,
                event_bus=self._event_bus,
                config=plugin_config,
            )
            try:
                await plugin.startup(context)
                logger.info("Plugin '%s' started", name)
            except Exception:
                logger.exception("Plugin '%s' startup failed", name)

        await self._event_bus.emit(
            Event(type=LifecycleEvent.STARTUP, source="plugin_manager")
        )

    async def shutdown(self) -> None:
        """Emit SHUTDOWN, then call shutdown() on all plugins in reverse order."""
        await self._event_bus.emit(
            Event(type=LifecycleEvent.SHUTDOWN, source="plugin_manager")
        )
        for name, plugin in reversed(list(self._plugins.items())):
            try:
                await plugin.shutdown()
                logger.info("Plugin '%s' shut down", name)
            except Exception:
                logger.exception("Plugin '%s' shutdown failed", name)

    # ── Accessors ──────────────────────────────────────────────────────────────

    def get(self, name: str) -> PluginBase | None:
        return self._plugins.get(name)

    def list_loaded(self) -> list[str]:
        return list(self._plugins.keys())

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return metadata for every discovered plugin, including load status."""
        result: list[dict[str, Any]] = []
        for name in self.discover():
            plugin_dir = self._plugins_dir / name
            toml = load_plugin_toml(plugin_dir)
            meta: dict[str, Any] = dict(toml.get("plugin", {}))
            meta["directory"] = name
            meta["loaded"] = name in self._plugins
            result.append(meta)
        return result

    # ── Internals ──────────────────────────────────────────────────────────────

    def _validate_metadata(self, plugin_name: str, meta: dict[str, Any]) -> None:
        missing = _REQUIRED_META - set(meta.keys())
        if missing:
            raise PluginMetadataError(
                f"Plugin '{plugin_name}' plugin.toml [plugin] section "
                f"is missing required fields: {sorted(missing)}"
            )
