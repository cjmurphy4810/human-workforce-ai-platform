"""Tests for the ServiceRegistry (DI container)."""

from __future__ import annotations

import pytest
from plugin_sdk.di import ServiceRegistry
from plugin_sdk.exceptions import ServiceNotFoundError


def test_register_and_get() -> None:
    reg = ServiceRegistry()
    reg.register("db", "mock_db")
    assert reg.get("db") == "mock_db"


def test_get_returns_none_for_missing_service() -> None:
    reg = ServiceRegistry()
    assert reg.get("missing") is None


def test_require_returns_registered_service() -> None:
    reg = ServiceRegistry()
    reg.register("config", {"key": "value"})
    assert reg.require("config") == {"key": "value"}


def test_require_raises_for_missing_service() -> None:
    reg = ServiceRegistry()
    with pytest.raises(ServiceNotFoundError, match="not registered"):
        reg.require("missing")


def test_has_returns_true_for_registered() -> None:
    reg = ServiceRegistry()
    reg.register("x", 1)
    assert reg.has("x") is True


def test_has_returns_false_for_missing() -> None:
    reg = ServiceRegistry()
    assert reg.has("missing") is False


def test_list_services_returns_sorted_names() -> None:
    reg = ServiceRegistry()
    reg.register("zebra", 1)
    reg.register("alpha", 2)
    reg.register("mango", 3)
    assert reg.list_services() == ["alpha", "mango", "zebra"]


def test_register_overwrites_existing_service() -> None:
    reg = ServiceRegistry()
    reg.register("key", "first")
    reg.register("key", "second")
    assert reg.require("key") == "second"


def test_services_can_hold_any_type() -> None:
    reg = ServiceRegistry()
    reg.register("int", 42)
    reg.register("list", [1, 2, 3])
    reg.register("dict", {"a": "b"})
    assert reg.require("int") == 42
    assert reg.require("list") == [1, 2, 3]
    assert reg.require("dict") == {"a": "b"}


def test_require_error_message_includes_available_services() -> None:
    reg = ServiceRegistry()
    reg.register("alpha", 1)
    with pytest.raises(ServiceNotFoundError, match="alpha"):
        reg.require("missing")
