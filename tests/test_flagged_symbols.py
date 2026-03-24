"""Tests for FlaggedSymbols query parsing and client methods."""

from dataclasses import FrozenInstanceError

import pytest

from tickerscope._exceptions import APIError
from tickerscope._models import WatchlistDetail, WatchlistSymbol
from tickerscope._parsing import parse_watchlist_detail_response


def test_parse_watchlist_detail_response(flagged_symbols_response) -> None:
    """Parse fixture into WatchlistDetail with correct items."""
    result = parse_watchlist_detail_response(
        flagged_symbols_response, "100000000000001"
    )

    assert result.id == "100000000000001"
    assert result.name == "My Watchlist"
    assert result.last_modified == "2026-01-15T10:00:00.000Z"
    assert result.description is None
    assert len(result.items) == 3
    assert result.items[0].key == "aabbcc001122334455667788"
    assert result.items[0].dow_jones_key == "13-111111"


def test_parse_watchlist_detail_not_found() -> None:
    """Raise APIError when watchlist data is null."""
    with pytest.raises(APIError, match="not found"):
        parse_watchlist_detail_response({"data": {"watchlist": None}}, "missing-id")


def test_parse_watchlist_detail_graphql_errors() -> None:
    """Raise APIError when response contains GraphQL errors."""
    with pytest.raises(APIError):
        parse_watchlist_detail_response(
            {"errors": [{"message": "forbidden"}]}, "some-id"
        )


def test_watchlist_item_frozen() -> None:
    """WatchlistSymbol is immutable (frozen dataclass)."""
    item = WatchlistSymbol(key="abc123", dow_jones_key="13-111111")

    with pytest.raises(FrozenInstanceError):
        item.key = "changed"  # type: ignore[misc]


def test_watchlist_detail_frozen() -> None:
    """WatchlistDetail is immutable (frozen dataclass)."""
    detail = WatchlistDetail(
        id="1", name="Test", last_modified=None, description=None, items=[]
    )

    with pytest.raises(FrozenInstanceError):
        detail.name = "changed"  # type: ignore[misc]
