"""Tests for MarketDataScreen query parsing and client methods."""

from dataclasses import FrozenInstanceError

import pytest

from tickerscope._exceptions import APIError
from tickerscope._models import ScreenResult
from tickerscope._parsing import parse_screen_result_response


def test_parse_screen_result_response(screen_result_response) -> None:
    """Parse fixture into ScreenResult with correct row data."""
    result = parse_screen_result_response(screen_result_response)

    assert result.screen_name == "MarketSurge.Test.FakeScreen"
    assert result.elapsed_time == "0.123"
    assert result.num_instruments == 3
    assert len(result.rows) == 2
    assert result.rows[0]["Symbol"] == "FAKE"
    assert result.rows[0]["CompanyName"] == "Fake Corp"
    assert result.rows[0]["CompositeRating"] == "99"
    assert result.rows[1]["Symbol"] == "TEST"


def test_parse_screen_result_empty() -> None:
    """Return ScreenResult with empty rows when responseValues is empty."""
    raw = {
        "data": {
            "marketDataScreen": {
                "screenName": "SomeScreen",
                "elapsedTime": "0.001",
                "numberOfInstrumentsInSource": 0,
                "responseValues": [],
            }
        }
    }
    result = parse_screen_result_response(raw)

    assert result.rows == []
    assert result.screen_name == "SomeScreen"


def test_parse_screen_result_null_data() -> None:
    """Raise APIError when marketDataScreen is null."""
    with pytest.raises(APIError):
        parse_screen_result_response({"data": {"marketDataScreen": None}})


def test_screen_result_frozen() -> None:
    """ScreenResult is immutable (frozen dataclass)."""
    result = ScreenResult(
        screen_name="Test", elapsed_time="0.1", num_instruments=0, rows=[]
    )

    with pytest.raises(FrozenInstanceError):
        result.screen_name = "changed"  # type: ignore[misc]
