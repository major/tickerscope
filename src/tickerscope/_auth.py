"""Authentication helpers for the MarketSurge API."""

import base64
import json
import logging
import os
import time

import httpx
import rookiepy  # pyright: ignore[reportMissingImports]

from tickerscope._exceptions import AuthenticationError, CookieExtractionError

_log = logging.getLogger("tickerscope")

GRAPHQL_URL = "https://shared-data.dowjones.io/gateway/graphql"
CLIENT_URL = "https://www.investors.com/client"
DYLAN_TOKEN = "x4ckyhshg90pdq6bwf6n1voijs7r3fdk"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0"
)


def authenticate(browser: str = "firefox", timeout: float = 30.0) -> str:
    """Extract cookies from browser and exchange them for a MarketSurge JWT.

    Args:
        browser: Browser name supported by rookiepy (e.g. "firefox", "chrome").
        timeout: HTTP request timeout in seconds.

    Raises:
        CookieExtractionError: If rookiepy fails to extract cookies.
        AuthenticationError: If the JWT exchange fails or user is not logged in.

    Returns:
        JWT token string for use in Authorization header.
    """
    try:
        extractor = getattr(rookiepy, browser)
    except AttributeError:
        raise CookieExtractionError(
            f"Browser {browser!r} is not supported by rookiepy",
            browser=browser,
        )

    try:
        raw_cookies = extractor(["investors.com"])
    except Exception as exc:
        raise CookieExtractionError(
            f"Failed to extract cookies from {browser!r}: {exc}",
            browser=browser,
        ) from exc

    cookie_jar = {c["name"]: c["value"] for c in raw_cookies}

    headers = {
        "User-Agent": USER_AGENT,
        "x-encrypted-document-key": "",
        "x-original-host": "marketsurge-beta.investors.com",
        "x-original-referrer": "",
        "x-original-url": "/mstool",
        "Referer": "https://marketsurge-beta.investors.com/",
        "Origin": "https://marketsurge-beta.investors.com",
    }

    try:
        resp = httpx.get(
            CLIENT_URL, headers=headers, cookies=cookie_jar, timeout=timeout
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AuthenticationError(f"JWT exchange request failed: {exc}") from exc

    data = resp.json()

    if not data.get("isLoggedIn"):
        raise AuthenticationError(
            "Not logged in -- make sure you're signed into MarketSurge in the browser."
        )

    _log.info("Authenticated as %s %s", data.get("given_name"), data.get("family_name"))
    return data["jwt"]


def resolve_jwt(
    jwt: str | None = None, browser: str = "firefox", timeout: float = 30.0
) -> str:
    """Resolve JWT using precedence chain: jwt param > TICKERSCOPE_JWT env var > browser auth.

    Args:
        jwt: Direct JWT token string.
        browser: Browser name for cookie extraction fallback.
        timeout: HTTP timeout for auth request fallback.

    Returns:
        JWT token string.

    Raises:
        CookieExtractionError: If browser cookie extraction fails.
        AuthenticationError: If JWT exchange fails or user not logged in.
    """
    if jwt:
        return jwt

    env_jwt = os.environ.get("TICKERSCOPE_JWT", "")
    if env_jwt:
        return env_jwt

    return authenticate(browser=browser, timeout=timeout)


def is_token_expired(token: str, *, clock_skew: int = 30) -> bool:
    """Check if a JWT token's exp claim has passed.

    Args:
        token: JWT token string to check.
        clock_skew: Seconds of leeway to allow for clock drift (default: 30).

    Returns:
        True if the token is expired or malformed, False if still valid.
        Malformed/non-JWT tokens are treated as expired (fail-safe).
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return True
        # Add padding for base64 decoding
        payload_b64 = parts[1] + "=" * (4 - len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
        exp = payload.get("exp")
        if exp is None:
            return True
        return time.time() >= (exp - clock_skew)
    except Exception:
        return True


async def async_resolve_jwt(
    jwt: str | None = None, browser: str = "firefox", timeout: float = 30.0
) -> str:
    """Async version of resolve_jwt, uses async_authenticate() as the fallback.

    Args:
        jwt: Direct JWT token string.
        browser: Browser name for cookie extraction fallback.
        timeout: HTTP timeout for auth request fallback.

    Returns:
        JWT token string.

    Raises:
        CookieExtractionError: If browser cookie extraction fails.
        AuthenticationError: If JWT exchange fails or user not logged in.
    """
    if jwt:
        return jwt

    env_jwt = os.environ.get("TICKERSCOPE_JWT", "")
    if env_jwt:
        return env_jwt

    return await async_authenticate(browser=browser, timeout=timeout)


async def async_authenticate(browser: str = "firefox", timeout: float = 30.0) -> str:
    """Async version of authenticate(), uses httpx.AsyncClient for the JWT exchange.

    Cookie extraction via rookiepy remains synchronous (reads local files).
    Only the HTTP request to CLIENT_URL is async.

    Args:
        browser: Browser name supported by rookiepy (e.g. "firefox", "chrome").
        timeout: HTTP request timeout in seconds.

    Raises:
        CookieExtractionError: If rookiepy fails to extract cookies.
        AuthenticationError: If the JWT exchange fails or user is not logged in.

    Returns:
        JWT token string for use in Authorization header.
    """
    try:
        extractor = getattr(rookiepy, browser)
    except AttributeError:
        raise CookieExtractionError(
            f"Browser {browser!r} is not supported by rookiepy",
            browser=browser,
        )

    try:
        raw_cookies = extractor(["investors.com"])
    except Exception as exc:
        raise CookieExtractionError(
            f"Failed to extract cookies from {browser!r}: {exc}",
            browser=browser,
        ) from exc

    cookie_jar = {c["name"]: c["value"] for c in raw_cookies}

    headers = {
        "User-Agent": USER_AGENT,
        "x-encrypted-document-key": "",
        "x-original-host": "marketsurge-beta.investors.com",
        "x-original-referrer": "",
        "x-original-url": "/mstool",
        "Referer": "https://marketsurge-beta.investors.com/",
        "Origin": "https://marketsurge-beta.investors.com",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                CLIENT_URL, headers=headers, cookies=cookie_jar, timeout=timeout
            )
            resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AuthenticationError(f"JWT exchange request failed: {exc}") from exc

    data = resp.json()

    if not data.get("isLoggedIn"):
        raise AuthenticationError(
            "Not logged in -- make sure you're signed into MarketSurge in the browser."
        )

    _log.info("Authenticated as %s %s", data.get("given_name"), data.get("family_name"))
    return data["jwt"]
