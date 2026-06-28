"""Shared fixtures and sys.path setup for plugin_sdk tests."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parents[3]
_SDK_DIR = _REPO_ROOT / "plugin-sdk"

if str(_SDK_DIR) not in sys.path:
    sys.path.insert(0, str(_SDK_DIR))
