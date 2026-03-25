"""Custom exception hierarchy for TickerScope library."""

from __future__ import annotations

from typing import Any


class TickerScopeError(Exception):
    """Base exception for all TickerScope library errors."""

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return "An unexpected error occurred."

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {
            "error_type": "tickerscope_error",
            "message": str(self),
            "user_message": self.user_message,
        }


class AuthenticationError(TickerScopeError):
    """Raised when authentication fails (cookie extraction or JWT exchange)."""

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return "Authentication failed. Check your credentials and try again."

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {
            "error_type": "authentication_error",
            "message": str(self),
            "user_message": self.user_message,
        }


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

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        if self.browser is not None:
            return f"Could not extract cookies from {self.browser}. Log into MarketSurge in {self.browser} first."
        return (
            "No browser cookies found. Log into MarketSurge in Firefox or Chrome first."
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        d: dict[str, Any] = {
            "error_type": "cookie_extraction_error",
            "message": str(self),
            "user_message": self.user_message,
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

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return "Authentication token expired. Re-authenticate to continue."

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        d: dict[str, Any] = {
            "error_type": "token_expired",
            "message": str(self),
            "user_message": self.user_message,
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

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message including GraphQL error details."""
        base = f"MarketSurge API error: {str(self)}"
        if self.errors:
            details = "; ".join(e.get("message", str(e)) for e in self.errors)
            return f"{base} - Details: {details}"
        return base

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {
            "error_type": "api_error",
            "message": str(self),
            "errors": self.errors,
            "user_message": self.user_message,
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

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        if self.symbol is not None:
            return f"Symbol '{self.symbol}' not found. Check the ticker spelling."
        return "Symbol not found. Check the ticker spelling."

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        d: dict[str, Any] = {
            "error_type": "symbol_not_found",
            "message": str(self),
            "user_message": self.user_message,
        }
        if self.symbol is not None:
            d["symbol"] = self.symbol
        return d


class HTTPError(TickerScopeError):
    """Raised when an HTTP request returns a non-401/403 error status code.

    Attributes:
        status_code: HTTP status code from the response.
        response_body: Raw response body text.
        message: Error message describing the HTTP error.
    """

    def __init__(
        self,
        *,
        status_code: int,
        response_body: str,
        message: str,
    ) -> None:
        """Initialize HTTPError.

        Args:
            status_code: HTTP status code from the response.
            response_body: Raw response body text.
            message: Error message describing the HTTP error.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.message = message

    @property
    def user_message(self) -> str:
        """Return a user-friendly error message."""
        return f"MarketSurge returned an HTTP {self.status_code} error."

    def to_dict(self) -> dict[str, Any]:
        """Return a structured dict representation of this error."""
        return {
            "error_type": "http_error",
            "status_code": self.status_code,
            "message": self.message,
            "response_body": self.response_body,
            "user_message": self.user_message,
        }
