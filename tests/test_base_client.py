"""Tests for BaseTickerScopeClient abstraction."""

# pyright: reportMissingImports=false

import pytest

from tickerscope import AsyncTickerScopeClient, BaseTickerScopeClient, TickerScopeClient


def test_base_client_is_exported() -> None:
    """BaseTickerScopeClient is importable from the public module."""
    assert BaseTickerScopeClient is not None


def test_base_client_is_abstract() -> None:
    """BaseTickerScopeClient cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseTickerScopeClient()  # type: ignore[abstract]


def test_sync_client_inherits_base_client() -> None:
    """TickerScopeClient subclasses BaseTickerScopeClient."""
    assert issubclass(TickerScopeClient, BaseTickerScopeClient)


def test_async_client_inherits_base_client() -> None:
    """AsyncTickerScopeClient subclasses BaseTickerScopeClient."""
    assert issubclass(AsyncTickerScopeClient, BaseTickerScopeClient)


def test_sync_context_manager_works() -> None:
    """Sync client can be used as context manager."""
    with TickerScopeClient(jwt="fake") as client:
        assert isinstance(client, TickerScopeClient)
        assert client._http is not None

    assert client._http.is_closed


@pytest.mark.asyncio
async def test_async_context_manager_works() -> None:
    """Async client can be used as async context manager."""
    async with AsyncTickerScopeClient(jwt="fake") as client:
        assert isinstance(client, AsyncTickerScopeClient)
        assert client._http is not None

    assert client._http.is_closed
