"""Tests for the custom exception hierarchy."""


from tickerscope._exceptions import (
    APIError,
    AuthenticationError,
    CookieExtractionError,
    TickerScopeError,
    SymbolNotFoundError,
)


class TestTickerScopeError:
    """Tests for TickerScopeError base exception."""

    def test_message_preserved(self) -> None:
        """Test that exception message is preserved."""
        exc = TickerScopeError("test msg")
        assert str(exc) == "test msg"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_inheritance_from_tickerscope_error(self) -> None:
        """Test that AuthenticationError inherits from TickerScopeError."""
        exc = AuthenticationError("auth failed")
        assert isinstance(exc, TickerScopeError)


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
