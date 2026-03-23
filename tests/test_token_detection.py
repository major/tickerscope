"""Tests for 401/403 HTTP error detection in _graphql() and is_token_expired property."""

from unittest.mock import patch

import httpx
import pytest
import respx

from tickerscope._auth import GRAPHQL_URL
from tickerscope._client import AsyncTickerScopeClient, TickerScopeClient
from tickerscope._exceptions import AuthenticationError, TokenExpiredError

FAKE_JWT = "fake.jwt.token"


@pytest.fixture
def sync_client():
    """Create a sync client with mocked JWT resolution."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = TickerScopeClient(jwt=FAKE_JWT)
    yield client
    client.close()


@pytest.fixture
async def async_client():
    """Create an async client with mocked JWT resolution."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient(jwt=FAKE_JWT)
    yield client
    await client.aclose()


# ── Sync client tests ──────────────────────────────────────────────


@respx.mock
def test_graphql_401_raises_token_expired_error(sync_client):
    """Test that HTTP 401 raises TokenExpiredError with status_code attribute."""
    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(401))
    with pytest.raises(TokenExpiredError) as exc_info:
        sync_client._graphql({"query": "{ test }"})
    assert exc_info.value.status_code == 401


@respx.mock
def test_graphql_403_raises_authentication_error(sync_client):
    """Test that HTTP 403 raises AuthenticationError, NOT TokenExpiredError."""
    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(403))
    with pytest.raises(AuthenticationError) as exc_info:
        sync_client._graphql({"query": "{ test }"})
    assert not isinstance(exc_info.value, TokenExpiredError)


@respx.mock
def test_graphql_500_still_raises_httpx_error(sync_client):
    """Test that HTTP 500 still raises httpx.HTTPStatusError (no wrapping)."""
    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        sync_client._graphql({"query": "{ test }"})


def test_is_token_expired_property_returns_bool(sync_client):
    """Test that is_token_expired property delegates to _auth.is_token_expired."""
    with patch(
        "tickerscope._client._is_token_expired", return_value=True
    ) as mock_check:
        result = sync_client.is_token_expired
    assert result is True
    mock_check.assert_called_once_with(FAKE_JWT)


# ── Async client tests ─────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_async_graphql_401_raises_token_expired_error(async_client):
    """Test that async HTTP 401 raises TokenExpiredError with status_code."""
    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(401))
    with pytest.raises(TokenExpiredError) as exc_info:
        await async_client._graphql({"query": "{ test }"})
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@respx.mock
async def test_async_graphql_403_raises_authentication_error(async_client):
    """Test that async HTTP 403 raises AuthenticationError, NOT TokenExpiredError."""
    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(403))
    with pytest.raises(AuthenticationError) as exc_info:
        await async_client._graphql({"query": "{ test }"})
    assert not isinstance(exc_info.value, TokenExpiredError)


@pytest.mark.asyncio
@respx.mock
async def test_async_graphql_500_still_raises_httpx_error(async_client):
    """Test that async HTTP 500 still raises httpx.HTTPStatusError (no wrapping)."""
    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(httpx.HTTPStatusError):
        await async_client._graphql({"query": "{ test }"})
