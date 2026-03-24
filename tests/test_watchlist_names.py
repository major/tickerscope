"""Tests for GetAllWatchlistNames query parsing and client methods."""

from dataclasses import FrozenInstanceError

import pytest

from tickerscope._exceptions import APIError
from tickerscope._parsing import parse_watchlists_response
from tickerscope._models import WatchlistSummary


def test_parse_watchlists_response(watchlist_names_response) -> None:
    """Parse fixture into WatchlistSummary list with correct field values."""
    result = parse_watchlists_response(watchlist_names_response)

    assert len(result) == 2
    assert result[0].id == 100000000000001
    assert result[0].name == "My Watchlist"
    assert result[0].last_modified == "2026-01-15T10:00:00.000Z"
    assert result[0].description is None
    assert result[1].name == "Tech Stocks"
    assert result[1].description == "Technology sector picks"


def test_parse_watchlist_names_empty() -> None:
    """Return empty list when watchlists array is empty."""
    result = parse_watchlists_response({"data": {"watchlists": []}})

    assert result == []


def test_parse_watchlist_names_graphql_errors() -> None:
    """Raise APIError when response contains GraphQL errors."""
    with pytest.raises(APIError):
        parse_watchlists_response({"errors": [{"message": "unauthorized"}]})


def test_watchlist_summary_frozen() -> None:
    """WatchlistSummary is immutable (frozen dataclass)."""
    summary = WatchlistSummary(
        id=1, name="Test", last_modified="2026-01-01T00:00:00Z", description=None
    )

    with pytest.raises(FrozenInstanceError):
        summary.name = "Changed"  # type: ignore[misc]
