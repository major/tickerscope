"""Tests for RSRatingRIPanel (RS rating history) endpoint."""

# pyright: reportMissingImports=false

import pytest
import respx
import httpx

from tickerscope._parsing import parse_rs_rating_history_response
from tickerscope._models import RSRatingHistory, RSRatingSnapshot
from tickerscope._exceptions import APIError

GRAPHQL_URL = "https://shared-data.dowjones.io/gateway/graphql"


def test_parse_rs_rating_history_fixture(rs_rating_history_response) -> None:
    """Parse real RS rating history fixture into RSRatingHistory."""
    result = parse_rs_rating_history_response(rs_rating_history_response, "TEST")
    assert result.symbol == "TEST"
    assert len(result.ratings) == 8
    assert result.rs_line_new_high is False
    current = [
        r for r in result.ratings if r.period_offset == "CURRENT" and r.period == "P12M"
    ]
    assert len(current) == 1
    assert current[0].value == 90
    assert isinstance(result.ratings[0], RSRatingSnapshot)


def test_parse_rs_rating_history_empty_ratings() -> None:
    """Return RSRatingHistory with empty list when rsRating array is empty."""
    raw = {
        "data": {
            "marketData": [
                {
                    "id": "1",
                    "ratings": {"rsRating": []},
                    "pricingStatistics": {
                        "intradayStatistics": {"rsLineNewHigh": True}
                    },
                }
            ]
        }
    }
    result = parse_rs_rating_history_response(raw, "EMPTY")
    assert result.ratings == []
    assert result.rs_line_new_high is True


def test_parse_rs_rating_history_missing_intraday_stats() -> None:
    """Set rs_line_new_high to None when intradayStatistics is absent."""
    raw = {
        "data": {
            "marketData": [
                {
                    "id": "1",
                    "ratings": {
                        "rsRating": [
                            {
                                "letterValue": "NONE",
                                "period": "P12M",
                                "periodOffset": "CURRENT",
                                "value": 85,
                            }
                        ]
                    },
                    "pricingStatistics": {},
                }
            ]
        }
    }
    result = parse_rs_rating_history_response(raw, "NOSTAT")
    assert result.rs_line_new_high is None
    assert len(result.ratings) == 1


def test_rs_rating_history_frozen() -> None:
    """RSRatingHistory is immutable (frozen dataclass)."""
    snap = RSRatingSnapshot(
        letter_value="NONE", period="P12M", period_offset="CURRENT", value=90
    )
    history = RSRatingHistory(symbol="TEST", ratings=[snap], rs_line_new_high=False)
    with pytest.raises(AttributeError):
        history.symbol = "OTHER"  # type: ignore


def test_rs_rating_snapshot_frozen() -> None:
    """RSRatingSnapshot is immutable (frozen dataclass)."""
    snap = RSRatingSnapshot(
        letter_value="NONE", period="P12M", period_offset="CURRENT", value=90
    )
    with pytest.raises(AttributeError):
        snap.value = 95  # type: ignore


@respx.mock
def test_get_rs_rating_history_sync(sync_client, rs_rating_history_response) -> None:
    """Sync get_rs_rating_history returns RSRatingHistory."""
    route = respx.post(GRAPHQL_URL).mock(
        return_value=httpx.Response(200, json=rs_rating_history_response)
    )
    result = sync_client.get_rs_rating_history("TEST")
    assert result.symbol == "TEST"
    assert len(result.ratings) == 8
    assert route.call_count == 1


@respx.mock
async def test_get_rs_rating_history_async(
    async_client, rs_rating_history_response
) -> None:
    """Async get_rs_rating_history returns RSRatingHistory."""
    respx.post(GRAPHQL_URL).mock(
        return_value=httpx.Response(200, json=rs_rating_history_response)
    )
    result = await async_client.get_rs_rating_history("TEST")
    assert result.symbol == "TEST"
    assert len(result.ratings) == 8


def test_parse_rs_rating_history_graphql_error() -> None:
    """Parser raises APIError when response contains GraphQL errors."""
    errors = [{"message": "bad query"}]
    with pytest.raises(APIError) as exc_info:
        parse_rs_rating_history_response({"errors": errors}, "TEST")
    assert exc_info.value.errors == errors


def test_parse_rs_rating_history_missing_symbol() -> None:
    """Parser raises SymbolNotFoundError when marketData is empty."""
    from tickerscope._exceptions import SymbolNotFoundError

    raw = {"data": {"marketData": []}}
    with pytest.raises(SymbolNotFoundError) as exc_info:
        parse_rs_rating_history_response(raw, "NOTFOUND")
    assert exc_info.value.symbol == "NOTFOUND"


def test_rs_rating_snapshot_serialization() -> None:
    """RSRatingSnapshot can be serialized to dict and JSON."""
    snap = RSRatingSnapshot(
        letter_value="NONE", period="P12M", period_offset="CURRENT", value=90
    )
    d = snap.to_dict()
    assert d == {
        "letter_value": "NONE",
        "period": "P12M",
        "period_offset": "CURRENT",
        "value": 90,
    }
    json_str = snap.to_json()
    assert "NONE" in json_str
    assert "90" in json_str


def test_rs_rating_history_serialization() -> None:
    """RSRatingHistory can be serialized to dict and JSON."""
    snap = RSRatingSnapshot(
        letter_value="NONE", period="P12M", period_offset="CURRENT", value=90
    )
    history = RSRatingHistory(symbol="TEST", ratings=[snap], rs_line_new_high=False)
    d = history.to_dict()
    assert d["symbol"] == "TEST"
    assert d["rs_line_new_high"] is False
    assert len(d["ratings"]) == 1
    assert d["ratings"][0]["value"] == 90
