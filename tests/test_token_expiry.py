"""Tests for TokenExpiredError exception and is_token_expired utility."""

import base64
import json
import time


from tickerscope import (
    TokenExpiredError,
    AuthenticationError,
    TickerScopeError,
    is_token_expired,
)


def _make_jwt(exp: int) -> str:
    """Build a minimal JWT with a specific exp claim."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = (
        base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode())
        .rstrip(b"=")
        .decode()
    )
    sig = base64.urlsafe_b64encode(b"fake-sig").rstrip(b"=").decode()
    return f"{header}.{payload}.{sig}"


class TestTokenExpiredError:
    """Tests for TokenExpiredError exception."""

    def test_token_expired_error_inherits_authentication_error(self) -> None:
        """Test that TokenExpiredError inherits from AuthenticationError."""
        e = TokenExpiredError("expired", status_code=401)
        assert isinstance(e, AuthenticationError)

    def test_token_expired_error_inherits_tickerscope_error(self) -> None:
        """Test that TokenExpiredError inherits from TickerScopeError."""
        e = TokenExpiredError("expired", status_code=401)
        assert isinstance(e, TickerScopeError)

    def test_token_expired_error_stores_status_code(self) -> None:
        """Test that status_code attribute is set when provided."""
        e = TokenExpiredError("expired", status_code=401)
        assert e.status_code == 401

    def test_token_expired_error_status_code_optional(self) -> None:
        """Test that status_code attribute is None when not provided."""
        e = TokenExpiredError("expired")
        assert e.status_code is None


class TestIsTokenExpired:
    """Tests for is_token_expired utility function."""

    def test_is_token_expired_returns_true_for_past_exp(self) -> None:
        """Test that expired token (past exp) returns True."""
        jwt = _make_jwt(int(time.time()) - 3600)
        assert is_token_expired(jwt) is True

    def test_is_token_expired_returns_false_for_future_exp(self) -> None:
        """Test that valid token (future exp) returns False."""
        jwt = _make_jwt(int(time.time()) + 3600)
        assert is_token_expired(jwt) is False

    def test_is_token_expired_returns_true_for_malformed_string(self) -> None:
        """Test that malformed JWT string returns True."""
        assert is_token_expired("not.a.jwt") is True

    def test_is_token_expired_returns_true_for_empty_string(self) -> None:
        """Test that empty string returns True."""
        assert is_token_expired("") is True

    def test_is_token_expired_returns_true_for_no_exp_claim(self) -> None:
        """Test that JWT without exp claim returns True."""
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
        payload = (
            base64.urlsafe_b64encode(b'{"sub":"user"}').rstrip(b"=").decode()
        )  # no exp
        sig = base64.urlsafe_b64encode(b"sig").rstrip(b"=").decode()
        jwt = f"{header}.{payload}.{sig}"
        assert is_token_expired(jwt) is True
