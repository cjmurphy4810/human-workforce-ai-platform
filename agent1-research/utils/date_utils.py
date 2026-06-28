from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)


def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def date_label(dt: datetime | None = None) -> str:
    """Return YYYY-MM-DD string in UTC."""
    target = dt or utcnow()
    return target.strftime("%Y-%m-%d")


def is_within_days(dt: datetime, days: int) -> bool:
    """True if dt falls within the last N days (UTC)."""
    return (utcnow() - to_utc(dt)).days < days
