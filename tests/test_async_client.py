"""Tests for AsyncTickerScopeClient."""

import inspect

import httpx
import pytest
import respx
from unittest.mock import patch

from tickerscope._client import AsyncTickerScopeClient


FAKE_JWT = "fake_async_jwt_token"


@pytest.fixture
async def async_client():
    """Create AsyncTickerScopeClient with mocked auth."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient()
    yield client
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_async_get_stock(async_client, stock_response):
    """Test async get_stock returns StockData with correct symbol and ratings."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=stock_response)
    )
    stock = await async_client.get_stock("TEST")
    assert stock.symbol == "TEST"
    assert stock.ratings.composite == 95


@pytest.mark.asyncio
@respx.mock
async def test_async_screen_watchlist(async_client):
    """Test async screen_watchlist returns list of WatchlistEntry."""
    mock_response = {
        "data": {
            "marketDataAdhocScreen": {
                "responseValues": [
                    [
                        {"mdItem": {"name": "Symbol"}, "value": "AAPL"},
                        {"mdItem": {"name": "CompositeRating"}, "value": 95},
                    ]
                ]
            }
        }
    }
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=mock_response)
    )
    entries = await async_client.screen_watchlist(12345)
    assert len(entries) == 1
    assert entries[0].symbol == "AAPL"


@pytest.mark.asyncio
@respx.mock
async def test_async_get_ownership(async_client):
    """Test async get_ownership returns OwnershipData with correct fields."""
    mock_response = {
        "data": {
            "marketData": [
                {
                    "ownership": {
                        "fundsFloatPercentHeld": {"formattedValue": "55.1%"},
                        "fundOwnershipSummary": [],
                    }
                }
            ]
        }
    }
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=mock_response)
    )
    result = await async_client.get_ownership("MSFT")
    assert result.symbol == "MSFT"
    assert result.funds_float_pct == "55.1%"


@pytest.mark.asyncio
async def test_async_context_manager():
    """Test that async context manager closes client on exit."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        async with AsyncTickerScopeClient() as client:
            assert client._http is not None
    assert client._http.is_closed


def test_async_client_methods_are_coroutines():
    """Test that all public methods are coroutines (async def)."""
    assert inspect.iscoroutinefunction(AsyncTickerScopeClient.get_stock)
    assert inspect.iscoroutinefunction(AsyncTickerScopeClient.screen_watchlist)
    assert inspect.iscoroutinefunction(AsyncTickerScopeClient.get_ownership)
    assert inspect.iscoroutinefunction(AsyncTickerScopeClient.aclose)
