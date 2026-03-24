"""Tests for Screens query parsing and client methods."""

from dataclasses import FrozenInstanceError

import pytest

from tickerscope._models import Screen, ScreenSource
from tickerscope._parsing import parse_screens_response


def test_parse_screens_response(screens_response) -> None:
    """Parse fixture into Screen list with nested ScreenSource."""
    result = parse_screens_response(screens_response)

    assert len(result) == 2
    assert result[0].id == "01AAAAAAAAAAAAAAAAAAAAAAAA"
    assert result[0].name == "My Growth Screen"
    assert result[0].type == "StockScreen"
    assert isinstance(result[0].source, ScreenSource)
    assert result[0].source.id == "100000000000001"
    assert result[0].source.type == "WATCHLIST"
    assert result[0].description == "High growth stocks"
    assert result[0].filter_criteria is None


def test_parse_screens_empty() -> None:
    """Return empty list when screens array is empty."""
    result = parse_screens_response({"data": {"user": {"screens": []}}})

    assert result == []


def test_parse_screens_null_source(screens_response) -> None:
    """Screen with null source has source=None."""
    result = parse_screens_response(screens_response)

    assert result[1].source is None
    assert result[1].name == "IBD 50"


def test_screen_frozen() -> None:
    """Screen is immutable (frozen dataclass)."""
    screen = Screen(
        id="1",
        name="Test",
        type="StockScreen",
        source=None,
        description=None,
        filter_criteria=None,
        created_at=None,
        updated_at=None,
    )

    with pytest.raises(FrozenInstanceError):
        screen.name = "changed"  # type: ignore[misc]


def test_screen_source_frozen() -> None:
    """ScreenSource is immutable (frozen dataclass)."""
    source = ScreenSource(id="1", type="WATCHLIST", pub="msr")

    with pytest.raises(FrozenInstanceError):
        source.id = "changed"  # type: ignore[misc]
