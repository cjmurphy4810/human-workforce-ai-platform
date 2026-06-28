"""Event types for the plugin lifecycle event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class LifecycleEvent(StrEnum):
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    BEFORE_RESEARCH = "before_research"
    AFTER_RESEARCH = "after_research"
    BEFORE_SCORING = "before_scoring"
    AFTER_SCORING = "after_scoring"
    BEFORE_BRIEF = "before_brief"
    AFTER_BRIEF = "after_brief"


@dataclass
class Event:
    """Payload carried by the event bus.

    ``type`` is a free-form string; use LifecycleEvent values for built-in
    events.  ``data`` carries event-specific context; ``source`` names the
    emitting component for tracing.
    """

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    source: str = ""
