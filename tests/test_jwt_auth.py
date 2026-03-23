"""Tests for JWT resolution and client injection."""

from unittest.mock import AsyncMock, patch


from tickerscope._auth import async_resolve_jwt, resolve_jwt
from tickerscope._client import AsyncTickerScopeClient, TickerScopeClient


class TestResolveJwtPrecedence:
    """Tests for resolve_jwt() precedence chain."""

    def test_jwt_param_takes_priority_over_env(self, monkeypatch):
        """JWT param wins even when TICKERSCOPE_JWT env var is set."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "env-token")
        result = resolve_jwt(jwt="param-token")
        assert result == "param-token"

    def test_jwt_param_takes_priority_over_browser(self):
        """JWT param wins, authenticate() is never called."""
        with patch("tickerscope._auth.authenticate") as mock_auth:
            result = resolve_jwt(jwt="direct-token")
        assert result == "direct-token"
        mock_auth.assert_not_called()

    def test_env_var_used_when_no_jwt_param(self, monkeypatch):
        """TICKERSCOPE_JWT env var used when jwt param is None."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "env-token-456")
        result = resolve_jwt(jwt=None)
        assert result == "env-token-456"

    def test_env_var_used_when_jwt_param_empty(self, monkeypatch):
        """Empty string jwt param falls through to env var."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "env-token-789")
        result = resolve_jwt(jwt="")
        assert result == "env-token-789"

    def test_authenticate_called_when_no_jwt_no_env(self, monkeypatch):
        """Falls through to authenticate() when jwt=None and env var not set."""
        monkeypatch.delenv("TICKERSCOPE_JWT", raising=False)
        with patch(
            "tickerscope._auth.authenticate", return_value="auth-token"
        ) as mock_auth:
            result = resolve_jwt(jwt=None)
        assert result == "auth-token"
        mock_auth.assert_called_once()

    def test_empty_env_var_falls_through_to_browser(self, monkeypatch):
        """Empty TICKERSCOPE_JWT env var treated as missing."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "")
        with patch(
            "tickerscope._auth.authenticate", return_value="auth-token"
        ) as mock_auth:
            result = resolve_jwt(jwt=None)
        assert result == "auth-token"
        mock_auth.assert_called_once()


class TestAsyncResolveJwtPrecedence:
    """Tests for async_resolve_jwt() precedence chain."""

    async def test_jwt_param_takes_priority(self):
        """JWT param short-circuits, async_authenticate() never called."""
        with patch("tickerscope._auth.async_authenticate") as mock_auth:
            result = await async_resolve_jwt(jwt="async-direct")
        assert result == "async-direct"
        mock_auth.assert_not_called()

    async def test_env_var_fallback(self, monkeypatch):
        """TICKERSCOPE_JWT env var used when jwt param is None."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "async-env-token")
        with patch("tickerscope._auth.async_authenticate") as mock_auth:
            result = await async_resolve_jwt(jwt=None)
        assert result == "async-env-token"
        mock_auth.assert_not_called()

    async def test_falls_through_to_async_authenticate(self, monkeypatch):
        """Calls async_authenticate() when jwt=None and env var unset."""
        monkeypatch.delenv("TICKERSCOPE_JWT", raising=False)
        mock_auth = AsyncMock(return_value="async-auth-token")
        with patch("tickerscope._auth.async_authenticate", mock_auth):
            result = await async_resolve_jwt(jwt=None)
        assert result == "async-auth-token"
        mock_auth.assert_called_once()


class TestClientJwtInjection:
    """Tests for JWT injection into TickerScopeClient."""

    def test_sync_client_jwt_param_bypasses_auth(self):
        """TickerScopeClient(jwt=...) skips authenticate()."""
        with patch("tickerscope._auth.authenticate") as mock_auth:
            client = TickerScopeClient(jwt="injected-token")
        assert client._jwt == "injected-token"
        mock_auth.assert_not_called()
        client.close()

    def test_async_client_jwt_param_bypasses_auth(self):
        """AsyncTickerScopeClient(jwt=...) skips authenticate()."""
        with patch("tickerscope._auth.authenticate") as mock_auth:
            client = AsyncTickerScopeClient(jwt="injected-token")
        assert client._jwt == "injected-token"
        mock_auth.assert_not_called()

    def test_sync_client_env_var_fallback(self, monkeypatch):
        """TickerScopeClient uses TICKERSCOPE_JWT env var when no jwt= param."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "env-token")
        with patch("tickerscope._auth.authenticate") as mock_auth:
            client = TickerScopeClient()
        assert client._jwt == "env-token"
        mock_auth.assert_not_called()
        client.close()

    def test_async_client_env_var_fallback(self, monkeypatch):
        """AsyncTickerScopeClient uses TICKERSCOPE_JWT env var when no jwt= param."""
        monkeypatch.setenv("TICKERSCOPE_JWT", "env-token")
        with patch("tickerscope._auth.authenticate") as mock_auth:
            client = AsyncTickerScopeClient(jwt=None)
        assert client._jwt == "env-token"
        mock_auth.assert_not_called()

    def test_sync_client_browser_positional_still_works(self):
        """TickerScopeClient('chrome') positional call still works."""
        with patch(
            "tickerscope._auth.authenticate", return_value="fake-jwt"
        ) as mock_auth:
            client = TickerScopeClient("chrome")
        mock_auth.assert_called_once_with(browser="chrome", timeout=30.0)
        client.close()
