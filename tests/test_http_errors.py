"""Tests for HTTPError exception class and HTTP error wrapping in clients."""

from __future__ import annotations

import httpx
import pytest
import respx

from tickerscope._exceptions import HTTPError, TokenExpiredError, AuthenticationError
from tickerscope._client import TickerScopeClient, AsyncTickerScopeClient


class TestHTTPErrorAttributes:
    """Tests for HTTPError exception attributes and initialization."""

    def test_httperror_has_status_code_attribute(self) -> None:
        """Test that HTTPError stores status_code attribute."""
        exc = HTTPError(
            status_code=429, response_body="rate limited", message="Rate limited"
        )
        assert exc.status_code == 429

    def test_httperror_has_response_body_attribute(self) -> None:
        """Test that HTTPError stores response_body attribute."""
        exc = HTTPError(
            status_code=500, response_body="server error", message="Server error"
        )
        assert exc.response_body == "server error"

    def test_httperror_has_message_attribute(self) -> None:
        """Test that HTTPError stores message attribute."""
        exc = HTTPError(
            status_code=502, response_body="bad gateway", message="Bad gateway"
        )
        assert exc.message == "Bad gateway"

    def test_httperror_str_returns_message(self) -> None:
        """Test that str(HTTPError) returns the message."""
        exc = HTTPError(
            status_code=503, response_body="unavailable", message="Service unavailable"
        )
        assert str(exc) == "Service unavailable"


class TestHTTPErrorToDict:
    """Tests for HTTPError.to_dict() method."""

    def test_to_dict_includes_error_type(self) -> None:
        """Test that to_dict() includes error_type field."""
        exc = HTTPError(status_code=500, response_body="error", message="Server error")
        d = exc.to_dict()
        assert d["error_type"] == "http_error"

    def test_to_dict_includes_status_code(self) -> None:
        """Test that to_dict() includes status_code field."""
        exc = HTTPError(
            status_code=429, response_body="rate limited", message="Rate limited"
        )
        d = exc.to_dict()
        assert d["status_code"] == 429

    def test_to_dict_includes_message(self) -> None:
        """Test that to_dict() includes message field."""
        exc = HTTPError(status_code=500, response_body="error", message="Server error")
        d = exc.to_dict()
        assert d["message"] == "Server error"

    def test_to_dict_includes_response_body(self) -> None:
        """Test that to_dict() includes response_body field."""
        exc = HTTPError(
            status_code=500, response_body="internal server error", message="Error"
        )
        d = exc.to_dict()
        assert d["response_body"] == "internal server error"

    def test_to_dict_429_has_rate_limit_message(self) -> None:
        """Test that 429 status code gets special rate limit message."""
        exc = HTTPError(
            status_code=429,
            response_body="",
            message="Rate limited, retry after a delay",
        )
        d = exc.to_dict()
        assert "rate" in d["message"].lower()

    def test_to_dict_500_has_server_error_message(self) -> None:
        """Test that 5xx status codes get special server error message."""
        exc = HTTPError(
            status_code=500, response_body="", message="MarketSurge server error"
        )
        d = exc.to_dict()
        assert "server" in d["message"].lower()

    def test_to_dict_502_has_server_error_message(self) -> None:
        """Test that 502 status code gets special server error message."""
        exc = HTTPError(
            status_code=502, response_body="", message="MarketSurge server error"
        )
        d = exc.to_dict()
        assert "server" in d["message"].lower()


class TestHTTPErrorInheritance:
    """Tests for HTTPError inheritance and exception hierarchy."""

    def test_httperror_is_tickerscope_error(self) -> None:
        """Test that HTTPError is a TickerScopeError."""
        from tickerscope._exceptions import TickerScopeError

        exc = HTTPError(status_code=500, response_body="error", message="Error")
        assert isinstance(exc, TickerScopeError)

    def test_httperror_is_exception(self) -> None:
        """Test that HTTPError is an Exception."""
        exc = HTTPError(status_code=500, response_body="error", message="Error")
        assert isinstance(exc, Exception)


class TestSyncClientHTTPErrorWrapping:
    """Tests for TickerScopeClient wrapping HTTP errors in HTTPError."""

    @respx.mock
    def test_sync_client_wraps_429_in_httperror(self) -> None:
        """Test that sync client wraps 429 status in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(429, text="rate limited")
        )

        with pytest.raises(HTTPError) as exc_info:
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert exc_info.value.status_code == 429
        assert route.called

    @respx.mock
    def test_sync_client_wraps_500_in_httperror(self) -> None:
        """Test that sync client wraps 500 status in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(500, text="server error")
        )

        with pytest.raises(HTTPError) as exc_info:
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert exc_info.value.status_code == 500
        assert route.called

    @respx.mock
    def test_sync_client_wraps_502_in_httperror(self) -> None:
        """Test that sync client wraps 502 status in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(502, text="bad gateway")
        )

        with pytest.raises(HTTPError) as exc_info:
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert exc_info.value.status_code == 502
        assert route.called

    @respx.mock
    def test_sync_client_still_raises_token_expired_on_401(self) -> None:
        """Test that sync client still raises TokenExpiredError on 401."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(401, text="unauthorized")
        )

        with pytest.raises(TokenExpiredError):
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert route.called

    @respx.mock
    def test_sync_client_still_raises_authentication_error_on_403(self) -> None:
        """Test that sync client still raises AuthenticationError on 403."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(403, text="forbidden")
        )

        with pytest.raises(AuthenticationError):
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert route.called


class TestAsyncClientHTTPErrorWrapping:
    """Tests for AsyncTickerScopeClient wrapping HTTP errors in HTTPError."""

    @respx.mock
    async def test_async_client_wraps_429_in_httperror(self) -> None:
        """Test that async client wraps 429 status in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(429, text="rate limited")
        )

        with pytest.raises(HTTPError) as exc_info:
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert exc_info.value.status_code == 429
        assert route.called

    @respx.mock
    async def test_async_client_wraps_500_in_httperror(self) -> None:
        """Test that async client wraps 500 status in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(500, text="server error")
        )

        with pytest.raises(HTTPError) as exc_info:
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert exc_info.value.status_code == 500
        assert route.called

    @respx.mock
    async def test_async_client_wraps_502_in_httperror(self) -> None:
        """Test that async client wraps 502 status in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(502, text="bad gateway")
        )

        with pytest.raises(HTTPError) as exc_info:
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert exc_info.value.status_code == 502
        assert route.called

    @respx.mock
    async def test_async_client_still_raises_token_expired_on_401(self) -> None:
        """Test that async client still raises TokenExpiredError on 401."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(401, text="unauthorized")
        )

        with pytest.raises(TokenExpiredError):
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert route.called

    @respx.mock
    async def test_async_client_still_raises_authentication_error_on_403(self) -> None:
        """Test that async client still raises AuthenticationError on 403."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(403, text="forbidden")
        )

        with pytest.raises(AuthenticationError):
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert route.called
