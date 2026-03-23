"""Date and datetime parsing utilities for TickerScope API responses."""

from __future__ import annotations

import datetime


def parse_date(value: str | None) -> datetime.date | None:
    """Parse a DATE-ONLY string into a date object.

    Args:
        value: ISO date string like "2024-01-15", or None.

    Returns:
        datetime.date if parseable; None for None, empty string,
        sentinel "0001-01-01", or any unparseable value.
    """
    if not value or value == "0001-01-01":
        return None
    try:
        return datetime.date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def parse_datetime(value: str | None) -> datetime.datetime | None:
    """Parse an RFC 3339 datetime string into a timezone-aware datetime.

    Args:
        value: ISO datetime string like "2024-01-15T09:30:00Z" or
               "2024-01-15T10:00:00.000-04:00", or None.

    Returns:
        Timezone-aware datetime.datetime if parseable; None otherwise.
        Never returns a naive (tzinfo=None) datetime.
    """
    if not value:
        return None
    try:
        dt = datetime.datetime.fromisoformat(value)
        # Ensure timezone-aware
        if dt.tzinfo is None:
            return None
        return dt
    except (ValueError, TypeError):
        return None


def parse_date_list(values: list[str | None]) -> list[datetime.date | None]:
    """Parse a list of DATE-ONLY strings, preserving None elements.

    Args:
        values: List of ISO date strings or None values.

    Returns:
        List of datetime.date objects or None, same length as input.
    """
    return [parse_date(v) for v in values]
