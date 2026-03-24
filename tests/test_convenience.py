"""Tests for get_watchlist_by_name() and get_screen_by_name() convenience methods."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


# ── Sync: get_watchlist_by_name ───────────────────────────────────────


def test_get_watchlist_by_name_returns_detail(sync_client):
    """Return full WatchlistDetail when a matching name is found."""
    from tickerscope import WatchlistDetail, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = "abc123"
    mock_detail = MagicMock(spec=WatchlistDetail)

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])
    sync_client.get_watchlist_symbols = MagicMock(return_value=mock_detail)

    result = sync_client.get_watchlist_by_name("My Watchlist")
    assert result is mock_detail
    sync_client.get_watchlist_symbols.assert_called_once_with("abc123")


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
async def test_async_get_watchlist_by_name_returns_detail(async_client):
    """Return full WatchlistDetail when a matching name is found (async)."""
    from tickerscope import WatchlistDetail, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = "abc123"
    mock_detail = MagicMock(spec=WatchlistDetail)

    async_client.get_watchlist_names = AsyncMock(return_value=[mock_summary])
    async_client.get_watchlist_symbols = AsyncMock(return_value=mock_detail)

    result = await async_client.get_watchlist_by_name("My Watchlist")
    assert result is mock_detail
    async_client.get_watchlist_symbols.assert_called_once_with("abc123")


@pytest.mark.asyncio
async def test_async_get_watchlist_by_name_raises_on_not_found(async_client):
    """Raise APIError when no watchlist matches the given name (async)."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "Other Watchlist"
    mock_summary.id = "abc123"

    async_client.get_watchlist_names = AsyncMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="No watchlist found with name"):
        await async_client.get_watchlist_by_name("Missing Watchlist")


# ── Async: get_screen_by_name ────────────────────────────────────────


@pytest.mark.asyncio
async def test_async_get_screen_by_name_returns_screen(async_client):
    """Return the matching Screen object when found (async)."""
    from tickerscope import Screen

    mock_screen = MagicMock(spec=Screen)
    mock_screen.name = "My Growth Screen"

    async_client.get_screens = AsyncMock(return_value=[mock_screen])

    result = await async_client.get_screen_by_name("My Growth Screen")
    assert result is mock_screen


@pytest.mark.asyncio
async def test_async_get_screen_by_name_raises_on_not_found(async_client):
    """Raise APIError when no screen matches the given name (async)."""
    from tickerscope import APIError, Screen

    mock_screen = MagicMock(spec=Screen)
    mock_screen.name = "Other Screen"

    async_client.get_screens = AsyncMock(return_value=[mock_screen])

    with pytest.raises(APIError, match="No screen found with name"):
        await async_client.get_screen_by_name("Missing Screen")


# ── Sync: screen_watchlist_by_name ────────────────────────────────────


def test_screen_watchlist_by_name_returns_entries(sync_client):
    """Return list of WatchlistEntry when a matching name is found."""
    from tickerscope import WatchlistEntry, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = 123
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_entries = [mock_entry]

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])
    sync_client.get_watchlist = MagicMock(return_value=mock_entries)

    result = sync_client.screen_watchlist_by_name("My Watchlist")
    assert result is mock_entries
    sync_client.get_watchlist.assert_called_once_with(123, limit=None)


def test_screen_watchlist_by_name_with_limit(sync_client):
    """Pass limit parameter through to get_watchlist()."""
    from tickerscope import WatchlistEntry, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = 123
    mock_entries = [MagicMock(spec=WatchlistEntry)]

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])
    sync_client.get_watchlist = MagicMock(return_value=mock_entries)

    result = sync_client.screen_watchlist_by_name("My Watchlist", limit=10)
    assert result is mock_entries
    sync_client.get_watchlist.assert_called_once_with(123, limit=10)


def test_screen_watchlist_by_name_raises_on_not_found(sync_client):
    """Raise APIError when no watchlist matches the given name."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "Other Watchlist"
    mock_summary.id = 123

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="No watchlist found with name"):
        sync_client.screen_watchlist_by_name("Missing Watchlist")


def test_screen_watchlist_by_name_raises_on_none_id(sync_client):
    """Raise APIError when the matching watchlist has no ID."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = None

    sync_client.get_watchlist_names = MagicMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="has no ID"):
        sync_client.screen_watchlist_by_name("My Watchlist")


# ── Async: screen_watchlist_by_name ───────────────────────────────────


@pytest.mark.asyncio
async def test_async_screen_watchlist_by_name_returns_entries(async_client):
    """Return list of WatchlistEntry when a matching name is found (async)."""
    from tickerscope import WatchlistEntry, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = 123
    mock_entry = MagicMock(spec=WatchlistEntry)
    mock_entries = [mock_entry]

    async_client.get_watchlist_names = AsyncMock(return_value=[mock_summary])
    async_client.get_watchlist = AsyncMock(return_value=mock_entries)

    result = await async_client.screen_watchlist_by_name("My Watchlist")
    assert result is mock_entries
    async_client.get_watchlist.assert_called_once_with(123, limit=None)


@pytest.mark.asyncio
async def test_async_screen_watchlist_by_name_with_limit(async_client):
    """Pass limit parameter through to get_watchlist() (async)."""
    from tickerscope import WatchlistEntry, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = 123
    mock_entries = [MagicMock(spec=WatchlistEntry)]

    async_client.get_watchlist_names = AsyncMock(return_value=[mock_summary])
    async_client.get_watchlist = AsyncMock(return_value=mock_entries)

    result = await async_client.screen_watchlist_by_name("My Watchlist", limit=10)
    assert result is mock_entries
    async_client.get_watchlist.assert_called_once_with(123, limit=10)


@pytest.mark.asyncio
async def test_async_screen_watchlist_by_name_raises_on_not_found(async_client):
    """Raise APIError when no watchlist matches the given name (async)."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "Other Watchlist"
    mock_summary.id = 123

    async_client.get_watchlist_names = AsyncMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="No watchlist found with name"):
        await async_client.screen_watchlist_by_name("Missing Watchlist")


@pytest.mark.asyncio
async def test_async_screen_watchlist_by_name_raises_on_none_id(async_client):
    """Raise APIError when the matching watchlist has no ID (async)."""
    from tickerscope import APIError, WatchlistSummary

    mock_summary = MagicMock(spec=WatchlistSummary)
    mock_summary.name = "My Watchlist"
    mock_summary.id = None

    async_client.get_watchlist_names = AsyncMock(return_value=[mock_summary])

    with pytest.raises(APIError, match="has no ID"):
        await async_client.screen_watchlist_by_name("My Watchlist")
