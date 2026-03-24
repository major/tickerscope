"""Tests for WatchlistSummary.id type conversion from str to int."""

from __future__ import annotations

from tickerscope._parsing import parse_watchlists_response
from tickerscope._models import WatchlistSummary


def test_parse_watchlists_response_id_is_int(watchlist_names_response) -> None:
    """Parse fixture converts watchlist ID from string to int."""
    result = parse_watchlists_response(watchlist_names_response)

    assert len(result) == 2
    assert isinstance(result[0].id, int), f"Expected int, got {type(result[0].id)}"
    assert result[0].id == 100000000000001
    assert isinstance(result[1].id, int), f"Expected int, got {type(result[1].id)}"
    assert result[1].id == 100000000000002


def test_watchlist_summary_id_type_annotation() -> None:
    """WatchlistSummary.id field is typed as int | None."""
    summary = WatchlistSummary(
        id=123,
        name="Test",
        last_modified="2026-01-01T00:00:00Z",
        description=None,
    )

    assert isinstance(summary.id, int)
    assert summary.id == 123


def test_watchlist_summary_id_none() -> None:
    """WatchlistSummary.id can be None."""
    summary = WatchlistSummary(
        id=None,
        name="Test",
        last_modified="2026-01-01T00:00:00Z",
        description=None,
    )

    assert summary.id is None


def test_watchlist_summary_serialization_preserves_int_id() -> None:
    """WatchlistSummary.to_dict() preserves int ID."""
    summary = WatchlistSummary(
        id=456,
        name="Test",
        last_modified="2026-01-01T00:00:00Z",
        description=None,
    )

    data = summary.to_dict()
    assert data["id"] == 456
    assert isinstance(data["id"], int)
