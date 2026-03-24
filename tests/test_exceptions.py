"""Tests for the custom exception hierarchy."""

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

    def test_message_preserved(self) -> None:
        """Test that exception message is preserved."""
        exc = TickerScopeError("test msg")
        assert str(exc) == "test msg"

    def test_user_message_is_generic(self) -> None:
        """Test that user_message returns generic error message."""
        exc = TickerScopeError("test msg")
        assert exc.user_message == "An unexpected error occurred."


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_inheritance_from_tickerscope_error(self) -> None:
        """Test that AuthenticationError inherits from TickerScopeError."""
        exc = AuthenticationError("auth failed")
        assert isinstance(exc, TickerScopeError)

    def test_user_message_is_auth_failed(self) -> None:
        """Test that user_message returns authentication failure message."""
        exc = AuthenticationError("auth failed")
        assert (
            exc.user_message
            == "Authentication failed. Check your credentials and try again."
        )


class TestCookieExtractionError:
    """Tests for CookieExtractionError."""

    def test_inheritance_from_authentication_error(self) -> None:
        """Test that CookieExtractionError inherits from AuthenticationError."""
        exc = CookieExtractionError("no cookies")
        assert isinstance(exc, AuthenticationError)

    def test_inheritance_from_tickerscope_error(self) -> None:
        """Test that CookieExtractionError inherits from TickerScopeError."""
        exc = CookieExtractionError("no cookies")
        assert isinstance(exc, TickerScopeError)

    def test_browser_attribute_with_value(self) -> None:
        """Test that browser attribute is set when provided."""
        exc = CookieExtractionError("no browser", browser="firefox")
        assert exc.browser == "firefox"

    def test_browser_attribute_none_by_default(self) -> None:
        """Test that browser attribute is None when not provided."""
        exc = CookieExtractionError("no browser")
        assert exc.browser is None

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

    def test_inheritance_from_tickerscope_error(self) -> None:
        """Test that APIError inherits from TickerScopeError."""
        exc = APIError("api error")
        assert isinstance(exc, TickerScopeError)

    def test_errors_attribute_with_value(self) -> None:
        """Test that errors attribute is set when provided."""
        errors = [{"message": "bad"}]
        exc = APIError("oops", errors=errors)
        assert exc.errors == [{"message": "bad"}]

    def test_errors_attribute_defaults_to_empty_list(self) -> None:
        """Test that errors attribute defaults to empty list."""
        exc = APIError("oops")
        assert exc.errors == []

    def test_user_message_includes_error_message(self) -> None:
        """Test that user_message includes the API error message."""
        exc = APIError("Something broke")
        assert exc.user_message == "MarketSurge API error: Something broke"


class TestSymbolNotFoundError:
    """Tests for SymbolNotFoundError."""

    def test_inheritance_from_api_error(self) -> None:
        """Test that SymbolNotFoundError inherits from APIError."""
        exc = SymbolNotFoundError("FAKE not found")
        assert isinstance(exc, APIError)

    def test_inheritance_from_tickerscope_error(self) -> None:
        """Test that SymbolNotFoundError inherits from TickerScopeError."""
        exc = SymbolNotFoundError("FAKE not found")
        assert isinstance(exc, TickerScopeError)

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
