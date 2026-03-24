"""Tests for structured error output via to_dict() on all exception classes."""

from __future__ import annotations

from tickerscope._exceptions import (
    APIError,
    AuthenticationError,
    CookieExtractionError,
    TickerScopeError,
    SymbolNotFoundError,
    TokenExpiredError,
)


class TestTickerScopeErrorToDict:
    """Tests for TickerScopeError.to_dict() base method."""

    def test_to_dict_returns_error_type_and_message(self) -> None:
        """Test that base error returns correct error_type and message."""
        exc = TickerScopeError("base error")
        d = exc.to_dict()
        assert d["error_type"] == "tickerscope_error"
        assert d["message"] == "base error"
        assert d["user_message"] == "An unexpected error occurred."


class TestAuthenticationErrorToDict:
    """Tests for AuthenticationError.to_dict() override."""

    def test_to_dict_returns_authentication_error_type(self) -> None:
        """Test that authentication error overrides error_type."""
        exc = AuthenticationError("auth failed")
        d = exc.to_dict()
        assert d["error_type"] == "authentication_error"
        assert d["message"] == "auth failed"
        assert (
            d["user_message"]
            == "Authentication failed. Check your credentials and try again."
        )


class TestCookieExtractionErrorToDict:
    """Tests for CookieExtractionError.to_dict() with optional browser field."""

    def test_to_dict_with_browser(self) -> None:
        """Test that browser is included when provided."""
        exc = CookieExtractionError("failed", browser="firefox")
        d = exc.to_dict()
        assert d["error_type"] == "cookie_extraction_error"
        assert d["browser"] == "firefox"
        assert "suggestion" not in d
        assert (
            d["user_message"]
            == "Could not extract cookies from firefox. Log into MarketSurge in firefox first."
        )

    def test_to_dict_without_browser_omits_field(self) -> None:
        """Test that browser key is omitted when None."""
        exc = CookieExtractionError("failed")
        d = exc.to_dict()
        assert d["error_type"] == "cookie_extraction_error"
        assert "browser" not in d


class TestTokenExpiredErrorToDict:
    """Tests for TokenExpiredError.to_dict() with optional status_code field."""

    def test_to_dict_with_status_code(self) -> None:
        """Test that status_code is included when provided."""
        exc = TokenExpiredError("expired", status_code=401)
        d = exc.to_dict()
        assert d["error_type"] == "token_expired"
        assert d["status_code"] == 401
        assert "suggestion" not in d
        assert (
            d["user_message"]
            == "Authentication token expired. Re-authenticate to continue."
        )

    def test_to_dict_without_status_code_omits_field(self) -> None:
        """Test that status_code key is omitted when None."""
        exc = TokenExpiredError("expired")
        d = exc.to_dict()
        assert d["error_type"] == "token_expired"
        assert "status_code" not in d


class TestAPIErrorToDict:
    """Tests for APIError.to_dict() with errors list."""

    def test_to_dict_includes_errors_list(self) -> None:
        """Test that errors list is included in dict output."""
        errors = [{"message": "Not found"}]
        exc = APIError("API error", errors=errors)
        d = exc.to_dict()
        assert d["error_type"] == "api_error"
        assert d["errors"] == errors
        assert "user_message" in d


class TestSymbolNotFoundErrorToDict:
    """Tests for SymbolNotFoundError.to_dict() with optional symbol field."""

    def test_to_dict_with_symbol(self) -> None:
        """Test that symbol is included when provided."""
        exc = SymbolNotFoundError("Not found", symbol="XYZZ")
        d = exc.to_dict()
        assert d["error_type"] == "symbol_not_found"
        assert d["symbol"] == "XYZZ"
        assert "suggestion" not in d
        assert (
            d["user_message"] == "Symbol 'XYZZ' not found. Check the ticker spelling."
        )

    def test_to_dict_without_symbol_omits_field(self) -> None:
        """Test that symbol key is omitted when None."""
        exc = SymbolNotFoundError("Not found")
        d = exc.to_dict()
        assert d["error_type"] == "symbol_not_found"
        assert "symbol" not in d

    def test_symbol_attribute_stored(self) -> None:
        """Test that symbol attribute is accessible on the exception."""
        exc = SymbolNotFoundError("Not found", symbol="AAPL")
        assert exc.symbol == "AAPL"

    def test_backward_compatible_without_symbol_kwarg(self) -> None:
        """Test that old-style raise without symbol kwarg still works."""
        exc = SymbolNotFoundError("Symbol not found: 'XYZZ'")
        assert exc.symbol is None
