"""Tests for HTTPError exception class and HTTP error wrapping in clients."""

from __future__ import annotations

import httpx
import pytest
import respx

from tickerscope._exceptions import AuthenticationError, HTTPError, TokenExpiredError
from tickerscope._client import AsyncTickerScopeClient, TickerScopeClient


class TestHTTPErrorAttributes:
    """Tests for HTTPError exception attributes and initialization."""

    def test_httperror_stores_all_attributes_and_str(self) -> None:
        """Test that HTTPError stores status_code, response_body, message, and str."""
        exc = HTTPError(
            status_code=429, response_body="rate limited", message="Rate limited"
        )
        assert exc.status_code == 429
        assert exc.response_body == "rate limited"
        assert exc.message == "Rate limited"
        assert str(exc) == "Rate limited"


class TestHTTPErrorToDict:
    """Tests for HTTPError.to_dict() method."""

    def test_to_dict_includes_all_fields(self) -> None:
        """Test that to_dict() includes all expected fields with correct values."""
        exc = HTTPError(
            status_code=500,
            response_body="internal server error",
            message="Server error",
        )
        d = exc.to_dict()
        assert d["error_type"] == "http_error"
        assert d["status_code"] == 500
        assert d["message"] == "Server error"
        assert d["response_body"] == "internal server error"
        assert "user_message" in d

    @pytest.mark.parametrize(
        "status_code, message, expected_substr",
        [
            (429, "Rate limited, retry after a delay", "rate"),
            (500, "MarketSurge server error", "server"),
            (502, "MarketSurge server error", "server"),
        ],
        ids=["429-rate-limit", "500-server-error", "502-server-error"],
    )
    def test_to_dict_message_content(
        self, status_code: int, message: str, expected_substr: str
    ) -> None:
        """Test that to_dict() message contains expected content per status code."""
        exc = HTTPError(status_code=status_code, response_body="", message=message)
        d = exc.to_dict()
        assert expected_substr in d["message"].lower()


class TestHTTPErrorInheritance:
    """Tests for HTTPError inheritance and exception hierarchy."""

    def test_httperror_inherits_from_tickerscope_error_and_exception(self) -> None:
        """Test that HTTPError is both a TickerScopeError and an Exception."""
        from tickerscope._exceptions import TickerScopeError

        exc = HTTPError(status_code=500, response_body="error", message="Error")
        assert isinstance(exc, TickerScopeError)
        assert isinstance(exc, Exception)


class TestSyncClientHTTPErrorWrapping:
    """Tests for TickerScopeClient wrapping HTTP errors in HTTPError."""

    @respx.mock
    @pytest.mark.parametrize(
        "status_code, response_text",
        [(429, "rate limited"), (500, "server error"), (502, "bad gateway")],
        ids=["429", "500", "502"],
    )
    def test_sync_client_wraps_status_in_httperror(
        self, status_code: int, response_text: str
    ) -> None:
        """Test that sync client wraps non-auth error status codes in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(status_code, text=response_text)
        )

        with pytest.raises(HTTPError) as exc_info:
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert exc_info.value.status_code == status_code
        assert route.called

    @respx.mock
    @pytest.mark.parametrize(
        "status_code, response_text, expected_type",
        [
            (401, "unauthorized", TokenExpiredError),
            (403, "forbidden", AuthenticationError),
        ],
        ids=["401-token-expired", "403-auth-error"],
    )
    def test_sync_client_raises_auth_error_on_status(
        self, status_code: int, response_text: str, expected_type: type
    ) -> None:
        """Test that sync client raises specific auth errors for 401/403."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(status_code, text=response_text)
        )

        with pytest.raises(expected_type):
            client = TickerScopeClient(jwt="fake-jwt")
            client._graphql({"query": "test"})

        assert route.called


class TestAsyncClientHTTPErrorWrapping:
    """Tests for AsyncTickerScopeClient wrapping HTTP errors in HTTPError."""

    @respx.mock
    @pytest.mark.parametrize(
        "status_code, response_text",
        [(429, "rate limited"), (500, "server error"), (502, "bad gateway")],
        ids=["429", "500", "502"],
    )
    async def test_async_client_wraps_status_in_httperror(
        self, status_code: int, response_text: str
    ) -> None:
        """Test that async client wraps non-auth error status codes in HTTPError."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(status_code, text=response_text)
        )

        with pytest.raises(HTTPError) as exc_info:
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert exc_info.value.status_code == status_code
        assert route.called

    @respx.mock
    @pytest.mark.parametrize(
        "status_code, response_text, expected_type",
        [
            (401, "unauthorized", TokenExpiredError),
            (403, "forbidden", AuthenticationError),
        ],
        ids=["401-token-expired", "403-auth-error"],
    )
    async def test_async_client_raises_auth_error_on_status(
        self, status_code: int, response_text: str, expected_type: type
    ) -> None:
        """Test that async client raises specific auth errors for 401/403."""
        route = respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
            return_value=httpx.Response(status_code, text=response_text)
        )

        with pytest.raises(expected_type):
            client = AsyncTickerScopeClient(jwt="fake-jwt")
            await client._graphql({"query": "test"})
            await client.aclose()

        assert route.called
