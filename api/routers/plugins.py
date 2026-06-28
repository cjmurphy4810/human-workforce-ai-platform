"""Plugin management API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from api.dependencies import get_plugin_manager

router = APIRouter(prefix="/plugins", tags=["Plugins"])


@router.get(
    "",
    summary="List all plugins",
    description=(
        "Returns metadata for every discovered plugin, including whether it is "
        "currently loaded and active.  Plugins are discovered from the plugins/ "
        "directory at startup."
    ),
)
async def list_plugins(
    plugin_manager: Any = Depends(get_plugin_manager),
) -> dict[str, Any]:
    if plugin_manager is None:
        return {"plugins": [], "loaded": [], "total": 0}
    plugins = plugin_manager.list_plugins()
    loaded = plugin_manager.list_loaded()
    return {
        "plugins": plugins,
        "loaded": loaded,
        "total": len(plugins),
        "total_loaded": len(loaded),
    }
