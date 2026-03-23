"""Tests for get_watchlist_by_name() and get_screen_by_name() convenience methods."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

FAKE_JWT = "fake.jwt.token"


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def sync_client():
    """Create a sync TickerScopeClient with a fake JWT."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        from tickerscope import TickerScopeClient

        return TickerScopeClient(jwt=FAKE_JWT)


# ── Sync: get_watchlist_by_name ───────────────────────────────────────


def test_get_watchlist_by_name_returns_detail(sync_client):
    """Return full WatchlistDetail when a matching name is found."""
    from tickerscope import WatchlistDetail, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = "abc123"
    mock_detail = MagicMock(spec=WatchlistDetail)

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])
    sync_client.get_watchlist_items = MagicMock(return_value=mock_detail)

    result = sync_client.get_watchlist_by_name("My Watchlist")
    assert result is mock_detail
    sync_client.get_watchlist_items.assert_called_once_with("abc123")


def test_get_watchlist_by_name_raises_on_not_found(sync_client):
    """Raise APIError when no watchlist matches the given name."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "Other Watchlist"
    mock_summary.id = "abc123"

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="No watchlist found with name"):
        sync_client.get_watchlist_by_name("Missing Watchlist")


def test_get_watchlist_by_name_raises_on_none_id(sync_client):
    """Raise APIError when the matching watchlist has no ID."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = None

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="has no ID"):
        sync_client.get_watchlist_by_name("My Watchlist")


# ── Sync: get_screen_by_name ─────────────────────────────────────────


def test_get_screen_by_name_returns_screen(sync_client):
    """Return the matching Screen object when found."""
    from tickerscope import Screen

    mock_screen = MagicMock(spec=Screen)
    mock_screen.name = "My Growth Screen"

    sync_client.get_screens = MagicMock(return_value=[mock_screen])

    result = sync_client.get_screen_by_name("My Growth Screen")
    assert result is mock_screen


def test_get_screen_by_name_raises_on_not_found(sync_client):
    """Raise APIError when no screen matches the given name."""
    from tickerscope import APIError, Screen

    mock_screen = MagicMock(spec=Screen)
    mock_screen.name = "Other Screen"

    sync_client.get_screens = MagicMock(return_value=[mock_screen])

    with pytest.raises(APIError, match="No screen found with name"):
        sync_client.get_screen_by_name("Missing Screen")


# ── Async: get_watchlist_by_name ──────────────────────────────────────


@pytest.mark.asyncio
async def test_async_get_watchlist_by_name_returns_detail():
    """Return full WatchlistDetail when a matching name is found (async)."""
    from tickerscope import AsyncTickerScopeClient, WatchlistDetail, WatchlistSummary

    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient(jwt=FAKE_JWT)

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = "abc123"
    mock_detail = MagicMock(spec=WatchlistDetail)

    client.get_watchlist_names = AsyncMock(return_value=[mock_summary])
    client.get_watchlist_items = AsyncMock(return_value=mock_detail)

    result = await client.get_watchlist_by_name("My Watchlist")
    assert result is mock_detail
    client.get_watchlist_items.assert_called_once_with("abc123")
    await client.aclose()


@pytest.mark.asyncio
async def test_async_get_watchlist_by_name_raises_on_not_found():
    """Raise APIError when no watchlist matches the given name (async)."""
    from tickerscope import AsyncTickerScopeClient, APIError, WatchlistSummary

    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient(jwt=FAKE_JWT)

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "Other Watchlist"
    mock_summary.id = "abc123"

    client.get_watchlist_names = AsyncMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="No watchlist found with name"):
        await client.get_watchlist_by_name("Missing Watchlist")
    await client.aclose()


# ── Async: get_screen_by_name ────────────────────────────────────────


@pytest.mark.asyncio
async def test_async_get_screen_by_name_returns_screen():
    """Return the matching Screen object when found (async)."""
    from tickerscope import AsyncTickerScopeClient, Screen

    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient(jwt=FAKE_JWT)

    mock_screen = MagicMock(spec=Screen)
    mock_screen.name = "My Growth Screen"

    client.get_screens = AsyncMock(return_value=[mock_screen])

    result = await client.get_screen_by_name("My Growth Screen")
    assert result is mock_screen
    await client.aclose()


@pytest.mark.asyncio
async def test_async_get_screen_by_name_raises_on_not_found():
    """Raise APIError when no screen matches the given name (async)."""
    from tickerscope import AsyncTickerScopeClient, APIError, Screen

    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient(jwt=FAKE_JWT)

    mock_screen = MagicMock(spec=Screen)
    mock_screen.name = "Other Screen"

    client.get_screens = AsyncMock(return_value=[mock_screen])

    with pytest.raises(APIError, match="No screen found with name"):
        await client.get_screen_by_name("Missing Screen")
    await client.aclose()
