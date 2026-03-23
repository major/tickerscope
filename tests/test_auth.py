"""Tests for the authentication module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from tickerscope._auth import (
    CLIENT_URL,
    DYLAN_TOKEN,
    GRAPHQL_URL,
    USER_AGENT,
    authenticate,
)
from tickerscope._exceptions import AuthenticationError, CookieExtractionError


def _fake_cookies():
    """Return a minimal fake cookie list matching rookiepy's output format."""
    return [{"name": "session", "value": "abc123"}]


def _success_response():
    """Return a mock httpx.Response for a successful JWT exchange."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.json.return_value = {
        "isLoggedIn": True,
        "jwt": "fake_jwt_token",
        "given_name": "Test",
        "family_name": "User",
    }
    mock_resp.raise_for_status.return_value = None
    return mock_resp


class TestAuthenticateSuccess:
    """Tests for the happy-path authentication flow."""

    def test_authenticate_success(self):
        """Successful authentication returns the JWT string."""
        with (
            patch("tickerscope._auth.rookiepy") as mock_rookiepy,
            patch("tickerscope._auth.httpx.get", return_value=_success_response()),
        ):
            mock_rookiepy.firefox.return_value = _fake_cookies()
            result = authenticate(browser="firefox")

        assert result == "fake_jwt_token"

    def test_authenticate_default_browser_is_firefox(self):
        """Calling authenticate() with no args uses firefox by default."""
        with (
            patch("tickerscope._auth.rookiepy") as mock_rookiepy,
            patch("tickerscope._auth.httpx.get", return_value=_success_response()),
        ):
            mock_rookiepy.firefox.return_value = _fake_cookies()
            authenticate()

        mock_rookiepy.firefox.assert_called_once_with(["investors.com"])


class TestAuthenticateFailures:
    """Tests for authentication error paths."""

    def test_authenticate_not_logged_in(self):
        """Raise AuthenticationError when the server says isLoggedIn is false."""
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.json.return_value = {"isLoggedIn": False}
        mock_resp.raise_for_status.return_value = None

        with (
            patch("tickerscope._auth.rookiepy") as mock_rookiepy,
            patch("tickerscope._auth.httpx.get", return_value=mock_resp),
        ):
            mock_rookiepy.firefox.return_value = _fake_cookies()

            with pytest.raises(AuthenticationError, match="Not logged in"):
                authenticate()

    def test_authenticate_rookiepy_failure(self):
        """Raise CookieExtractionError when rookiepy raises during extraction."""
        with patch("tickerscope._auth.rookiepy") as mock_rookiepy:
            mock_rookiepy.firefox.side_effect = Exception("no cookies")

            with pytest.raises(CookieExtractionError) as exc_info:
                authenticate(browser="firefox")

        assert exc_info.value.browser == "firefox"

    def test_authenticate_invalid_browser(self):
        """Raise CookieExtractionError for an unsupported browser name."""
        with patch("tickerscope._auth.rookiepy") as mock_rookiepy:
            del mock_rookiepy.invalidbrowser99

            with pytest.raises(CookieExtractionError) as exc_info:
                authenticate(browser="invalidbrowser99")

        assert exc_info.value.browser == "invalidbrowser99"
        assert "not supported" in str(exc_info.value)

    def test_authenticate_http_error(self):
        """Raise AuthenticationError when the HTTP request fails."""
        mock_request = MagicMock(spec=httpx.Request)
        mock_response = MagicMock(spec=httpx.Response)

        with (
            patch("tickerscope._auth.rookiepy") as mock_rookiepy,
            patch(
                "tickerscope._auth.httpx.get",
                side_effect=httpx.HTTPStatusError(
                    "Server Error",
                    request=mock_request,
                    response=mock_response,
                ),
            ),
        ):
            mock_rookiepy.firefox.return_value = _fake_cookies()

            with pytest.raises(
                AuthenticationError, match="JWT exchange request failed"
            ):
                authenticate()


class TestConstants:
    """Tests to verify module-level constants are properly defined."""

    def test_constants_are_correct(self):
        """All constants have expected format and are non-empty."""
        assert GRAPHQL_URL.startswith("https://")
        assert CLIENT_URL.startswith("https://")
        assert len(DYLAN_TOKEN) > 0
        assert "Mozilla" in USER_AGENT
