"""Shared FastAPI dependencies.

Each function is injected via `Depends()`.  Tests replace them via
`app.dependency_overrides[get_repo] = lambda: mock_repo`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from fastapi import Request

# Imported lazily at runtime (after sys.path is set in api/main.py)
# to avoid circular import issues during module load.


def get_repo(request: Request) -> Any:
    """Return a live ArticleRepository backed by the shared session factory."""
    from storage.repository import ArticleRepository  # noqa: PLC0415

    return ArticleRepository(request.app.state.session_factory)


def get_config(request: Request) -> Any:
    """Return the loaded AppConfig from app state."""
    return request.app.state.config


def get_agent1_dir(request: Request) -> Path:
    """Return the agent1-research directory path from app state."""
    return cast(Path, request.app.state.agent1_dir)


def get_event_bus(request: Request) -> Any:
    """Return the EventBus, or None if the plugin system is not initialised."""
    return getattr(request.app.state, "event_bus", None)


def get_plugin_manager(request: Request) -> Any:
    """Return the PluginManager, or None if the plugin system is not initialised."""
    return getattr(request.app.state, "plugin_manager", None)
