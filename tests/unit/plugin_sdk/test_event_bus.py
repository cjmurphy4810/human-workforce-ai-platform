"""Tests for the EventBus."""

from __future__ import annotations

import pytest
from plugin_sdk.events.bus import EventBus
from plugin_sdk.events.types import Event, LifecycleEvent


@pytest.mark.asyncio
async def test_subscribe_and_emit() -> None:
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    bus.subscribe(LifecycleEvent.STARTUP, handler)
    await bus.emit(Event(type=LifecycleEvent.STARTUP))

    assert len(received) == 1
    assert received[0].type == LifecycleEvent.STARTUP


@pytest.mark.asyncio
async def test_failing_handler_does_not_block_others() -> None:
    bus = EventBus()
    calls: list[str] = []

    async def bad_handler(event: Event) -> None:
        raise RuntimeError("intentional error")

    async def good_handler(event: Event) -> None:
        calls.append("good")

    bus.subscribe(LifecycleEvent.STARTUP, bad_handler)
    bus.subscribe(LifecycleEvent.STARTUP, good_handler)

    await bus.emit(Event(type=LifecycleEvent.STARTUP))
    assert calls == ["good"]


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    calls: list[str] = []

    async def handler(event: Event) -> None:
        calls.append("called")

    bus.subscribe(LifecycleEvent.STARTUP, handler)
    bus.unsubscribe(LifecycleEvent.STARTUP, handler)
    await bus.emit(Event(type=LifecycleEvent.STARTUP))

    assert calls == []


@pytest.mark.asyncio
async def test_emit_with_no_subscribers_is_a_noop() -> None:
    bus = EventBus()
    await bus.emit(Event(type=LifecycleEvent.AFTER_RESEARCH))  # must not raise


@pytest.mark.asyncio
async def test_event_data_reaches_handler() -> None:
    bus = EventBus()
    payloads: list[dict] = []

    async def handler(event: Event) -> None:
        payloads.append(event.data)

    bus.subscribe(LifecycleEvent.AFTER_BRIEF, handler)
    await bus.emit(
        Event(type=LifecycleEvent.AFTER_BRIEF, data={"key": "value"})
    )

    assert payloads == [{"key": "value"}]


@pytest.mark.asyncio
async def test_multiple_handlers_all_called() -> None:
    bus = EventBus()
    calls: list[int] = []

    async def h1(event: Event) -> None:
        calls.append(1)

    async def h2(event: Event) -> None:
        calls.append(2)

    bus.subscribe(LifecycleEvent.STARTUP, h1)
    bus.subscribe(LifecycleEvent.STARTUP, h2)
    await bus.emit(Event(type=LifecycleEvent.STARTUP))

    assert calls == [1, 2]


def test_subscriber_count() -> None:
    bus = EventBus()

    async def h(event: Event) -> None: ...

    assert bus.subscriber_count(LifecycleEvent.STARTUP) == 0
    bus.subscribe(LifecycleEvent.STARTUP, h)
    assert bus.subscriber_count(LifecycleEvent.STARTUP) == 1
    bus.unsubscribe(LifecycleEvent.STARTUP, h)
    assert bus.subscriber_count(LifecycleEvent.STARTUP) == 0


@pytest.mark.asyncio
async def test_events_are_independent_per_type() -> None:
    bus = EventBus()
    startup_calls: list[str] = []
    shutdown_calls: list[str] = []

    async def on_startup(event: Event) -> None:
        startup_calls.append("s")

    async def on_shutdown(event: Event) -> None:
        shutdown_calls.append("d")

    bus.subscribe(LifecycleEvent.STARTUP, on_startup)
    bus.subscribe(LifecycleEvent.SHUTDOWN, on_shutdown)

    await bus.emit(Event(type=LifecycleEvent.STARTUP))
    assert startup_calls == ["s"]
    assert shutdown_calls == []

    await bus.emit(Event(type=LifecycleEvent.SHUTDOWN))
    assert shutdown_calls == ["d"]
