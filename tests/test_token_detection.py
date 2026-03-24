"""Tests for 401/403 HTTP error detection in _graphql() and is_token_expired property."""

from unittest.mock import patch

import httpx
import pytest
import respx

from tickerscope._auth import GRAPHQL_URL
from tickerscope._exceptions import AuthenticationError, TokenExpiredError


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
def test_graphql_500_raises_httperror(sync_client):
    """Test that HTTP 500 is wrapped in HTTPError."""
    from tickerscope._exceptions import HTTPError

    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(HTTPError):
        sync_client._graphql({"query": "{ test }"})


def test_is_token_expired_property_returns_bool(sync_client):
    """Test that is_token_expired property delegates to _auth.is_token_expired."""
    with patch(
        "tickerscope._client._is_token_expired", return_value=True
    ) as mock_check:
        result = sync_client.is_token_expired
    assert result is True
    mock_check.assert_called_once_with(sync_client._jwt)


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
async def test_async_graphql_500_raises_httperror(async_client):
    """Test that async HTTP 500 is wrapped in HTTPError."""
    from tickerscope._exceptions import HTTPError

    respx.post(GRAPHQL_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(HTTPError):
        await async_client._graphql({"query": "{ test }"})
