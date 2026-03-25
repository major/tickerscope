"""Tests for user_message branching logic and computed defaults in the exception hierarchy."""

from __future__ import annotations

from tickerscope._exceptions import (
    APIError,
    AuthenticationError,
    CookieExtractionError,
    HTTPError,
    TickerScopeError,
    SymbolNotFoundError,
    TokenExpiredError,
)


class TestTickerScopeError:
    """Tests for TickerScopeError base exception."""

    def test_user_message_is_generic(self) -> None:
        """Test that user_message returns generic error message."""
        exc = TickerScopeError("test msg")
        assert exc.user_message == "An unexpected error occurred."


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_user_message_is_auth_failed(self) -> None:
        """Test that user_message returns authentication failure message."""
        exc = AuthenticationError("auth failed")
        assert (
            exc.user_message
            == "Authentication failed. Check your credentials and try again."
        )


class TestCookieExtractionError:
    """Tests for CookieExtractionError user_message branching."""

    def test_user_message_with_browser(self) -> None:
        """Test that user_message includes browser name when set."""
        exc = CookieExtractionError("no cookies", browser="firefox")
        assert exc.user_message.startswith("Could not")
        assert "firefox" in exc.user_message

    def test_user_message_without_browser(self) -> None:
        """Test that user_message handles missing browser gracefully."""
        exc = CookieExtractionError("no cookies")
        assert exc.user_message.startswith("No browser cookies found")
        assert "None" not in exc.user_message


class TestAPIError:
    """Tests for APIError."""

    def test_errors_attribute_defaults_to_empty_list(self) -> None:
        """Test that errors attribute defaults to empty list."""
        exc = APIError("oops")
        assert exc.errors == []

    def test_user_message_includes_error_message(self) -> None:
        """Test that user_message includes the API error message."""
        exc = APIError("Something broke")
        assert exc.user_message == "MarketSurge API error: Something broke"


class TestSymbolNotFoundError:
    """Tests for SymbolNotFoundError user_message branching."""

    def test_user_message_with_symbol(self) -> None:
        """Test that user_message includes symbol when set."""
        exc = SymbolNotFoundError("not found", symbol="FAKE")
        assert exc.user_message == "Symbol 'FAKE' not found. Check the ticker spelling."

    def test_user_message_without_symbol(self) -> None:
        """Test that user_message handles missing symbol gracefully."""
        exc = SymbolNotFoundError("not found")
        assert "Symbol not found" in exc.user_message
        assert "None" not in exc.user_message


class TestTokenExpiredError:
    """Tests for TokenExpiredError."""

    def test_user_message_is_re_authenticate(self) -> None:
        """Test that user_message returns re-authentication message."""
        exc = TokenExpiredError("token expired")
        assert (
            exc.user_message
            == "Authentication token expired. Re-authenticate to continue."
        )


class TestHTTPError:
    """Tests for HTTPError."""

    def test_user_message_includes_status_code(self) -> None:
        """Test that user_message includes HTTP status code."""
        exc = HTTPError(status_code=500, response_body="err", message="err")
        assert "500" in exc.user_message
