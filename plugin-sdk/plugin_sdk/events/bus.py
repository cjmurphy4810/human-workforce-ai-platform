"""Async event bus — the sole communication channel between plugins."""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from plugin_sdk.events.types import Event

logger = logging.getLogger(__name__)

Handler = Callable[[Event], Coroutine[Any, Any, None]]


class EventBus:
    """Publish/subscribe bus for lifecycle and domain events.

    Plugins subscribe during ``startup()`` and unsubscribe during
    ``shutdown()``.  Handlers that raise are logged and skipped so that
    one broken plugin never silences the rest.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type].append(handler)
        logger.debug("subscribed %s → %s", event_type, _handler_name(handler))

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers[event_type] = [
            h for h in self._handlers[event_type] if h is not handler
        ]

    async def emit(self, event: Event) -> None:
        handlers = list(self._handlers.get(event.type, []))
        if not handlers:
            return
        logger.debug("emit %s → %d handler(s)", event.type, len(handlers))
        for handler in handlers:
            try:
                await handler(event)
            except Exception:
                logger.exception(
                    "handler %s raised for event %s",
                    _handler_name(handler),
                    event.type,
                )

    def subscriber_count(self, event_type: str) -> int:
        return len(self._handlers.get(event_type, []))


def _handler_name(handler: Handler) -> str:
    return getattr(handler, "__qualname__", repr(handler))
