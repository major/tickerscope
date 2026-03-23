"""Custom exception hierarchy for TickerScope library."""

from __future__ import annotations

from typing import Any


class TickerScopeError(Exception):
    """Base exception for all TickerScope library errors."""

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {"error_type": "tickerscope_error", "message": str(self)}


class AuthenticationError(TickerScopeError):
    """Raised when authentication fails (cookie extraction or JWT exchange)."""

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {"error_type": "authentication_error", "message": str(self)}


class CookieExtractionError(AuthenticationError):
    """Raised when rookiepy fails to extract cookies from a browser.

    Attributes:
        browser: Name of the browser that failed cookie extraction.
    """

    def __init__(self, message: str, browser: str | None = None) -> None:
        """Initialize CookieExtractionError.

        Args:
            message: Error message describing the extraction failure.
            browser: Optional name of the browser that failed extraction.
        """
        super().__init__(message)
        self.browser = browser

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        d: dict[str, Any] = {
            "error_type": "cookie_extraction_error",
            "message": str(self),
            "suggestion": "Ensure the specified browser is installed and you're logged into MarketSurge",
        }
        if self.browser is not None:
            d["browser"] = self.browser
        return d


class TokenExpiredError(AuthenticationError):
    """Raised when the JWT token has expired or been rejected (HTTP 401).

    Attributes:
        status_code: HTTP status code that triggered this error (usually 401).
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        """Initialize TokenExpiredError.

        Args:
            message: Error message describing the expiry.
            status_code: HTTP status code that triggered this error (usually 401).
        """
        super().__init__(message)
        self.status_code = status_code

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        d: dict[str, Any] = {
            "error_type": "token_expired",
            "message": str(self),
            "suggestion": "Obtain a fresh JWT token and reinitialize the client",
        }
        if self.status_code is not None:
            d["status_code"] = self.status_code
        return d


class APIError(TickerScopeError):
    """Raised when the GraphQL API returns errors (even on HTTP 200).

    Attributes:
        errors: List of GraphQL error dicts from the response body.
    """

    def __init__(self, message: str, errors: list[dict] | None = None) -> None:
        """Initialize APIError.

        Args:
            message: Error message describing the API error.
            errors: Optional list of GraphQL error dicts from the response body.
        """
        super().__init__(message)
        self.errors = errors or []

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {
            "error_type": "api_error",
            "message": str(self),
            "errors": self.errors,
        }


class SymbolNotFoundError(APIError):
    """Raised when the API returns empty marketData for a requested symbol.

    Attributes:
        symbol: The ticker symbol that was not found.
    """

    def __init__(
        self,
        message: str,
        *,
        symbol: str | None = None,
        errors: list[dict] | None = None,
    ) -> None:
        """Initialize SymbolNotFoundError.

        Args:
            message: Error message describing what was not found.
            symbol: The ticker symbol that was not found.
            errors: Optional list of GraphQL error dicts.
        """
        super().__init__(message, errors=errors)
        self.symbol = symbol

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        d: dict[str, Any] = {
            "error_type": "symbol_not_found",
            "message": str(self),
            "suggestion": "Check the ticker symbol spelling or try a different symbol",
        }
        if self.symbol is not None:
            d["symbol"] = self.symbol
        return d
