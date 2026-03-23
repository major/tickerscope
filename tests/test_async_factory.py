"""Tests for AsyncTickerScopeClient.create() factory method."""

import inspect
from unittest.mock import patch

import pytest

from tickerscope._client import AsyncTickerScopeClient
from tickerscope._exceptions import AuthenticationError


class TestAsyncFactoryMethod:
    """Tests for the create() classmethod."""

    async def test_create_with_jwt_returns_client(self):
        """create(jwt=...) returns initialized AsyncTickerScopeClient."""
        client = await AsyncTickerScopeClient.create(jwt="test-jwt")
        assert isinstance(client, AsyncTickerScopeClient)
        assert client._jwt == "test-jwt"
        assert client._http is not None
        await client.aclose()

    async def test_create_is_coroutine_function(self):
        """create() must be a coroutine function (async)."""
        assert inspect.iscoroutinefunction(AsyncTickerScopeClient.create)

    async def test_create_with_jwt_skips_authenticate(self):
        """create(jwt=...) never calls authenticate()."""
        with patch("tickerscope._auth.authenticate") as mock_auth:
            with patch("tickerscope._auth.async_authenticate") as mock_async_auth:
                client = await AsyncTickerScopeClient.create(jwt="direct-jwt")
        mock_auth.assert_not_called()
        mock_async_auth.assert_not_called()
        assert client._jwt == "direct-jwt"
        await client.aclose()

    async def test_create_with_env_var(self, monkeypatch):
        """create() uses TICKERSCOPE_JWT env var when no jwt= param."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "env-jwt-token")
        with patch("tickerscope._auth.async_authenticate") as mock_async_auth:
            client = await AsyncTickerScopeClient.create()
        assert client._jwt == "env-jwt-token"
        mock_async_auth.assert_not_called()
        await client.aclose()

    async def test_create_context_manager(self):
        """Factory-created client works as async context manager."""
        async with await AsyncTickerScopeClient.create(jwt="ctx-jwt") as client:
            assert client._jwt == "ctx-jwt"
            assert client._http is not None

    async def test_create_auth_error_propagates(self, monkeypatch):
        """AuthenticationError from async_authenticate propagates from create()."""
        monkeypatch.delenv("TICKERSCOPE_JWT", raising=False)
        with patch(
            "tickerscope._auth.async_authenticate",
            side_effect=AuthenticationError("Not logged in"),
        ):
            with pytest.raises(AuthenticationError, match="Not logged in"):
                await AsyncTickerScopeClient.create()
