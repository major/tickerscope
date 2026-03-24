"""Tests for the sync MarketSurge client."""

# pyright: reportMissingImports=false

from unittest.mock import patch

import httpx
import pytest
import respx  # pyright: ignore[reportMissingImports]

from tickerscope._client import TickerScopeClient  # pyright: ignore[reportMissingImports]

FAKE_JWT = "fake_jwt_token_for_testing"


@pytest.fixture
def client(stock_response):
    """Create a TickerScopeClient with mocked authentication."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        c = TickerScopeClient()
    yield c
    c.close()


@respx.mock
def test_get_stock_returns_stock_data(client, stock_response):
    """Test that get_stock() parses GraphQL response into StockData."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=stock_response)
    )

    stock = client.get_stock("TEST")

    assert stock.symbol == "TEST"
    assert stock.ratings is not None
    assert stock.ratings.composite == 95


@respx.mock
def test_screen_watchlist_returns_entries(client):
    """Test that screen_watchlist() parses GraphQL response into WatchlistEntry list."""
    mock_response = {
        "data": {
            "marketDataAdhocScreen": {
                "responseValues": [
                    [
                        {"mdItem": {"name": "Symbol"}, "value": "AAPL"},
                        {"mdItem": {"name": "CompanyName"}, "value": "Apple Inc"},
                        {"mdItem": {"name": "CompositeRating"}, "value": 95},
                    ]
                ]
            }
        }
    }
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    entries = client.screen_watchlist(12345)

    assert len(entries) == 1
    assert entries[0].symbol == "AAPL"


@respx.mock
def test_get_ownership_returns_ownership_data(client):
    """Test that get_ownership() parses GraphQL response into OwnershipData."""
    mock_response = {
        "data": {
            "marketData": [
                {
                    "ownership": {
                        "fundsFloatPercentHeld": {"formattedValue": "42.5%"},
                        "fundOwnershipSummary": [
                            {
                                "date": {"value": "2024-09-30"},
                                "numberOfFundsHeld": {"formattedValue": "1234"},
                            }
                        ],
                    }
                }
            ]
        }
    }
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=mock_response)
    )

    ownership = client.get_ownership("AAPL")

    assert ownership.symbol == "AAPL"
    assert ownership.funds_float_pct == "42.5%"


def test_context_manager_calls_close():
    """Test that context manager calls close() on exit."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        with TickerScopeClient() as client:
            assert client._http is not None

    assert client._http.is_closed


@respx.mock
def test_http_error_raises(client):
    """Test that HTTP errors propagate correctly."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(500)
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.get_stock("AAPL")


def test_client_api_surface():
    """Test that TickerScopeClient has the expected public API."""
    import inspect

    methods = [m for m in dir(TickerScopeClient) if not m.startswith("_")]
    assert "get_stock" in methods
    assert "screen_watchlist" in methods
    assert "get_ownership" in methods
    assert "close" in methods

    sig = inspect.signature(TickerScopeClient.__init__)
    params = list(sig.parameters.keys())
    assert "browser" in params
    assert "timeout" in params
