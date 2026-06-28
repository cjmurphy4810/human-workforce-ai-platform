"""Plugin configuration helpers.

Each plugin directory contains a ``plugin.toml`` with two sections:
  [plugin]   — metadata validated by PluginManager
  [config]   — arbitrary plugin-specific settings passed in PluginContext

A global ``plugins/plugins.toml`` can override ``enabled`` per plugin
and supply per-plugin config overrides under ``[<plugin_name>.config]``.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def load_plugin_toml(plugin_dir: Path) -> dict[str, Any]:
    """Load and parse the plugin.toml for a single plugin directory."""
    path = plugin_dir / "plugin.toml"
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)


def load_global_config(plugins_dir: Path) -> dict[str, Any]:
    """Load the optional top-level plugins/plugins.toml."""
    path = plugins_dir / "plugins.toml"
    if not path.exists():
        return {}
    with path.open("rb") as f:
        return tomllib.load(f)
