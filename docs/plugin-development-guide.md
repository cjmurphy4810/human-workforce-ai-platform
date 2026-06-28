# Plugin Development Guide

Human Workforce AI Platform — Plugin SDK

---

## Overview

The platform uses a plugin architecture so new capabilities can be added without touching core platform code. Every feature beyond research data storage is a plugin: the intelligence engine, all export formats, future AI providers, video generators, publishing destinations, and notification channels.

**Key invariants:**
- Plugins never import from each other directly — they communicate through the event bus.
- The core platform never imports from plugins — it discovers and loads them dynamically.
- A plugin failure never crashes the platform — the manager logs and moves on.

---

## Quick Start

The minimum plugin is three files:

```
plugins/
  my_plugin/
    __init__.py        ← empty
    plugin.py          ← Plugin class
    plugin.toml        ← metadata + config
```

**`plugin.toml`**

```toml
[plugin]
name        = "my_plugin"
version     = "1.0.0"
description = "What this plugin does"
author      = "Your Name"
type        = "export"       # analytics | export | research | notification | ...
enabled     = true

[config]
output_dir  = "data/exports/my_plugin"
```

**`plugin.py`**

```python
from __future__ import annotations
import logging
from plugin_sdk.base import PluginBase, PluginContext, PluginMetadata
from plugin_sdk.events.types import Event, LifecycleEvent

logger = logging.getLogger(__name__)

class Plugin(PluginBase):
    metadata = PluginMetadata(
        name="my_plugin",
        version="1.0.0",
        description="What this plugin does",
        author="Your Name",
        plugin_type="export",
    )

    async def startup(self, context: PluginContext) -> None:
        # Subscribe to events here.
        context.event_bus.subscribe(LifecycleEvent.AFTER_BRIEF, self._on_after_brief)
        logger.info("my_plugin started")

    async def shutdown(self) -> None:
        logger.info("my_plugin shut down")

    async def _on_after_brief(self, event: Event) -> None:
        report = event.data.get("report_dict", {})
        # Do something with the report.
```

That's it. Drop the directory into `plugins/` and restart the API — the plugin is auto-discovered, loaded, and its lifecycle managed automatically.

---

## Plugin SDK Reference

### `PluginBase`

Every plugin must subclass `PluginBase` and name its class `Plugin`.

| Member | Required | Description |
|--------|----------|-------------|
| `metadata` | class attr | `PluginMetadata` instance describing the plugin |
| `startup(context)` | yes | Called once at startup; subscribe to events here |
| `shutdown()` | yes | Called once at shutdown; release resources here |

### `PluginMetadata`

```python
@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    plugin_type: str
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True
```

`plugin_type` is free-form but should match one of the standard interface names:
`research`, `ai_provider`, `video`, `publishing`, `analytics`, `knowledge`, `notification`, `export`.

### `PluginContext`

Injected into `startup()`. Provides:

| Attribute | Type | Description |
|-----------|------|-------------|
| `context.services` | `ServiceRegistry` | Access platform services by name |
| `context.event_bus` | `EventBus` | Subscribe to / emit events |
| `context.config` | `dict[str, Any]` | Plugin config from `[config]` in plugin.toml |

### `ServiceRegistry`

```python
context.services.require("config")         # raises ServiceNotFoundError if missing
context.services.get("session_factory")    # returns None if missing
context.services.has("agent1_dir")         # bool check
context.services.list_services()           # sorted list of registered names
```

**Platform-registered services** (available to all plugins at startup):

| Name | Type | Description |
|------|------|-------------|
| `config` | `AppConfig` | Research pipeline config (sources, scoring weights, etc.) |
| `session_factory` | `async_sessionmaker` | SQLAlchemy async session factory |
| `agent1_dir` | `Path` | Path to the agent1-research directory |

### `EventBus`

```python
# Subscribe (do this in startup)
context.event_bus.subscribe("after_brief", self._handler)

# Unsubscribe (optional, do this in shutdown)
context.event_bus.unsubscribe("after_brief", self._handler)

# Emit a custom event (do this anywhere after startup)
from plugin_sdk.events.types import Event
await context.event_bus.emit(Event(type="my_custom_event", data={"key": "value"}))
```

Handlers must be `async def` and accept a single `Event` argument:

```python
async def _handler(self, event: Event) -> None:
    payload = event.data      # dict
    ts      = event.timestamp # datetime (UTC)
    source  = event.source    # str — which component emitted this
```

---

## Lifecycle Events

Events are emitted automatically by the platform. Subscribe to any of them in `startup()`.

| Event | `LifecycleEvent` value | Emitted by | `event.data` keys |
|-------|----------------------|------------|-------------------|
| `startup` | `STARTUP` | PluginManager (after all plugins start) | — |
| `shutdown` | `SHUTDOWN` | PluginManager (before plugins shut down) | — |
| `before_research` | `BEFORE_RESEARCH` | `/run` pipeline route | — |
| `after_research` | `AFTER_RESEARCH` | `/run` pipeline route | `articles_fetched`, `articles_new`, `article_count`, `sources_succeeded` |
| `before_brief` | `BEFORE_BRIEF` | `POST /intelligence/run` | — |
| `after_brief` | `AFTER_BRIEF` | `POST /intelligence/run` | `report_dict`, `output_dir`, `articles_analyzed`, `opportunities_detected`, `trends_identified` |
| `before_scoring` | `BEFORE_SCORING` | (reserved — not yet emitted) | — |
| `after_scoring` | `AFTER_SCORING` | (reserved — not yet emitted) | — |

---

## Plugin Interfaces

Use these when your plugin is a drop-in replacement for a platform capability. Subclass the interface instead of `PluginBase` directly.

```python
from plugin_sdk.interfaces import (
    ResearchPlugin,      # fetch_articles + score_articles
    AIProviderPlugin,    # complete + embed
    VideoPlugin,         # generate_script + render_video
    PublishingPlugin,    # publish + unpublish
    AnalyticsPlugin,     # track_event + get_metrics
    KnowledgePlugin,     # index + search
    NotificationPlugin,  # notify
)
```

Example — a Slack notification plugin:

```python
from plugin_sdk.interfaces import NotificationPlugin

class Plugin(NotificationPlugin):
    metadata = PluginMetadata(
        name="slack_notify",
        version="1.0.0",
        description="Sends intelligence summaries to Slack",
        author="Your Name",
        plugin_type="notification",
    )

    async def startup(self, context: PluginContext) -> None:
        self._webhook = context.config["webhook_url"]
        context.event_bus.subscribe(LifecycleEvent.AFTER_BRIEF, self._on_after_brief)

    async def shutdown(self) -> None: ...

    async def notify(self, message: str, channel: str, **kwargs: Any) -> None:
        import httpx
        async with httpx.AsyncClient() as client:
            await client.post(self._webhook, json={"text": message, "channel": channel})

    async def _on_after_brief(self, event: Event) -> None:
        summary = event.data.get("report_dict", {}).get("summary", {})
        await self.notify(
            f"Intelligence report ready: {summary.get('opportunities_detected', 0)} opportunities",
            channel="#ai-intelligence",
        )
```

---

## Configuration

### Per-plugin configuration (`plugin.toml [config]`)

```toml
[config]
output_dir  = "data/exports/my_plugin"
max_items   = 25
api_key     = ""          # override in plugins.toml or env
```

Values are available in `context.config` as a plain `dict[str, Any]`.

### Global overrides (`plugins/plugins.toml`)

```toml
# Disable a plugin without editing its directory
[markdown_export]
enabled = false

# Override a plugin's config values
[json_export.config]
output_dir = "/mnt/shared/exports/json"
fields     = ["summary", "opportunities"]
```

Global overrides merge with (and take precedence over) the plugin's own `[config]`.

### Enabling/disabling at deploy time

Set `enabled = false` in `plugins/plugins.toml` for any plugin you want to disable without removing its directory. The platform skips loading it at startup and logs a single info message.

---

## Example Plugins

Three reference implementations ship in `plugins/`:

| Plugin | Type | Event | Output |
|--------|------|-------|--------|
| `local_file_export` | export | `AFTER_BRIEF` | `data/exports/local_file_export/YYYY-MM-DD/intelligence_export.json` (full report) |
| `markdown_export` | export | `AFTER_BRIEF` | `data/exports/markdown_export/YYYY-MM-DD/intelligence_summary.md` |
| `json_export` | export | `AFTER_BRIEF` | `data/exports/json_export/YYYY-MM-DD/intelligence_export.json` (selected fields) |
| `intelligence_engine` | analytics | `AFTER_RESEARCH`, `AFTER_BRIEF` | Logs availability; pipeline triggered via `POST /intelligence/run` |

Study `plugins/local_file_export/plugin.py` for the simplest possible export plugin pattern.

---

## Consuming Plugin Outputs from AI Tools

The export plugins write files that are immediately consumable by external AI tools.

**Claude (via Projects):** Upload `intelligence_export.json` or `intelligence_summary.md` to a Claude Project. Claude can then answer questions about opportunities, trends, and recommendations directly.

**NotebookLM:** Upload `executive_intelligence.md` from `intelligence-engine/data/output/YYYY-MM-DD/` as a source. NotebookLM indexes the full report for Q&A and podcast generation.

**OpenAI / custom tools:** The `json_export` plugin writes a compact `intelligence_export.json` with configurable fields. Point any OpenAI assistant file-search tool at this file for retrieval-augmented generation.

**Local models (Ollama, LM Studio):** Pass `executive_intelligence.md` as context in a system prompt. The Markdown format is optimised for LLM readability.

---

## Plugin API

**`GET /plugins`** — list all discovered plugins and their load status:

```json
{
  "total": 4,
  "total_loaded": 4,
  "loaded": ["intelligence_engine", "json_export", "local_file_export", "markdown_export"],
  "plugins": [
    {
      "name": "intelligence_engine",
      "version": "1.0.0",
      "type": "analytics",
      "loaded": true,
      "directory": "intelligence_engine"
    }
  ]
}
```

---

## Plugin Checklist

Before submitting a new plugin:

- [ ] `plugin.toml` has all required fields: `name`, `version`, `description`, `author`, `type`
- [ ] Class inside `plugin.py` is named exactly `Plugin`
- [ ] `Plugin` subclasses `PluginBase` (or an interface)
- [ ] `startup()` subscribes to events; `shutdown()` is implemented (can be a no-op)
- [ ] No direct imports from other plugins
- [ ] No imports from `api/`, `agent1-research/`, or `intelligence-engine/` in the plugin itself (use services or events instead)
- [ ] Config keys read from `context.config`, not hardcoded
- [ ] Tested: plugin loads, starts, handles its event, shuts down
