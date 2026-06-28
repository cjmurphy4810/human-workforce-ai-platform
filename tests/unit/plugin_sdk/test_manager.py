"""Tests for the PluginManager."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.di import ServiceRegistry
from plugin_sdk.events.bus import EventBus
from plugin_sdk.exceptions import PluginLoadError, PluginMetadataError
from plugin_sdk.manager import PluginManager

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_manager(plugins_dir: Path) -> PluginManager:
    return PluginManager(
        plugins_dir=plugins_dir,
        services=ServiceRegistry(),
        event_bus=EventBus(),
    )


def _write_valid_toml(
    plugin_dir: Path,
    name: str,
    plugin_type: str = "export",
    enabled: bool = True,
) -> None:
    plugin_dir.mkdir(parents=True, exist_ok=True)
    enabled_str = "true" if enabled else "false"
    (plugin_dir / "plugin.toml").write_text(
        f'[plugin]\n'
        f'name = "{name}"\n'
        f'version = "0.1.0"\n'
        f'description = "Test plugin"\n'
        f'author = "Test"\n'
        f'type = "{plugin_type}"\n'
        f'enabled = {enabled_str}\n',
        encoding="utf-8",
    )


def _make_fake_plugin(name: str, plugin_type: str = "export") -> type[PluginBase]:
    class FakePlugin(PluginBase):
        metadata = PluginMetadata(
            name=name,
            version="0.1.0",
            description="Test",
            author="Test",
            plugin_type=plugin_type,
        )

        def __init__(self) -> None:
            self.started = False
            self.stopped = False

        async def startup(self, context: PluginContext) -> None:
            self.started = True

        async def shutdown(self) -> None:
            self.stopped = True

    return FakePlugin


def _mock_module(plugin_class: type[PluginBase]) -> Any:
    mod = MagicMock()
    mod.Plugin = plugin_class
    return mod


# ── Discovery ─────────────────────────────────────────────────────────────────


def test_discover_returns_dirs_that_have_plugin_toml(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "alpha", "alpha")
    _write_valid_toml(plugins_dir / "beta", "beta")

    assert set(_make_manager(plugins_dir).discover()) == {"alpha", "beta"}


def test_discover_ignores_dirs_without_plugin_toml(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    (plugins_dir / "bare_dir").mkdir()

    assert _make_manager(plugins_dir).discover() == []


def test_discover_ignores_underscore_prefixed_dirs(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "__pycache__", "bad")

    assert _make_manager(plugins_dir).discover() == []


def test_discover_returns_empty_when_plugins_dir_absent(tmp_path: Path) -> None:
    assert _make_manager(tmp_path / "missing").discover() == []


def test_discover_returns_sorted_names(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "zebra", "zebra")
    _write_valid_toml(plugins_dir / "alpha", "alpha")

    assert _make_manager(plugins_dir).discover() == ["alpha", "zebra"]


# ── Loading ───────────────────────────────────────────────────────────────────


def test_load_missing_directory_raises_plugin_load_error(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    with pytest.raises(PluginLoadError, match="not found"):
        _make_manager(plugins_dir).load("nonexistent")


def test_load_disabled_plugin_is_skipped(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "off_plugin", "off_plugin", enabled=False)

    mgr = _make_manager(plugins_dir)
    mgr.load("off_plugin")

    assert mgr.get("off_plugin") is None
    assert "off_plugin" not in mgr.list_loaded()


def test_load_validates_required_metadata_fields(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugin_dir = plugins_dir / "bad_plugin"
    plugin_dir.mkdir(parents=True)
    (plugin_dir / "plugin.toml").write_text(
        '[plugin]\nname = "bad"\n', encoding="utf-8"
    )

    with pytest.raises(PluginMetadataError, match="missing required fields"):
        _make_manager(plugins_dir).load("bad_plugin")


def test_load_raises_when_Plugin_class_is_none(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "noplugin", "noplugin")

    mock_module = MagicMock()
    mock_module.Plugin = None

    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", return_value=mock_module):
        with pytest.raises(PluginLoadError, match="must define a 'Plugin' class"):
            mgr.load("noplugin")


def test_load_raises_when_Plugin_is_not_PluginBase_subclass(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "wrongplugin", "wrongplugin")

    mock_module = MagicMock()
    mock_module.Plugin = str  # not a PluginBase subclass

    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", return_value=mock_module):
        with pytest.raises(PluginLoadError, match="must define a 'Plugin' class"):
            mgr.load("wrongplugin")


def test_load_succeeds_and_plugin_is_accessible(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "myplugin", "myplugin")

    FakePlugin = _make_fake_plugin("myplugin")
    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", return_value=_mock_module(FakePlugin)):
        mgr.load("myplugin")

    assert mgr.get("myplugin") is not None
    assert "myplugin" in mgr.list_loaded()


# ── list_plugins ──────────────────────────────────────────────────────────────


def test_list_plugins_shows_loaded_and_unloaded(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "loaded", "loaded")
    _write_valid_toml(plugins_dir / "unloaded", "unloaded")

    FakePlugin = _make_fake_plugin("loaded")
    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", return_value=_mock_module(FakePlugin)):
        mgr.load("loaded")

    statuses = {p["directory"]: p["loaded"] for p in mgr.list_plugins()}
    assert statuses["loaded"] is True
    assert statuses["unloaded"] is False


# ── Lifecycle ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_startup_calls_plugin_startup(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "plug", "plug")

    FakePlugin = _make_fake_plugin("plug")
    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", return_value=_mock_module(FakePlugin)):
        mgr.load("plug")

    await mgr.startup()

    plugin = mgr.get("plug")
    assert plugin is not None
    assert plugin.started is True  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_shutdown_calls_plugin_shutdown(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "plug", "plug")

    FakePlugin = _make_fake_plugin("plug")
    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", return_value=_mock_module(FakePlugin)):
        mgr.load("plug")

    await mgr.startup()
    await mgr.shutdown()

    plugin = mgr.get("plug")
    assert plugin is not None
    assert plugin.stopped is True  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_startup_emits_startup_event(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()

    event_bus = EventBus()
    received: list[str] = []

    async def on_startup(event: Any) -> None:
        received.append(event.type)

    from plugin_sdk.events.types import LifecycleEvent

    event_bus.subscribe(LifecycleEvent.STARTUP, on_startup)

    mgr = PluginManager(
        plugins_dir=plugins_dir,
        services=ServiceRegistry(),
        event_bus=event_bus,
    )
    await mgr.startup()

    assert LifecycleEvent.STARTUP in received


@pytest.mark.asyncio
async def test_load_all_skips_failed_plugin_and_continues(tmp_path: Path) -> None:
    plugins_dir = tmp_path / "plugins"
    _write_valid_toml(plugins_dir / "good_plugin", "good_plugin")
    _write_valid_toml(plugins_dir / "bad_plugin", "bad_plugin")

    FakeGood = _make_fake_plugin("good_plugin")

    def side_effect(name: str) -> Any:
        if "good_plugin" in name:
            return _mock_module(FakeGood)
        raise ImportError("import failed")

    mgr = _make_manager(plugins_dir)
    with patch("importlib.import_module", side_effect=side_effect):
        mgr.load_all()

    assert "good_plugin" in mgr.list_loaded()
    assert "bad_plugin" not in mgr.list_loaded()
