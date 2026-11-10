"""Strict timestamp utilities for GXP source and server times."""

from __future__ import annotations

from datetime import UTC, datetime

from .errors import InvalidTimestamp


def parse_instant(value: object, field_name: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise InvalidTimestamp(field_name)
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidTimestamp(field_name) from exc
    if parsed.tzinfo is None:
        raise InvalidTimestamp(field_name)
    return parsed.astimezone(UTC)


def format_instant(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def utc_now() -> datetime:
    return datetime.now(UTC)

