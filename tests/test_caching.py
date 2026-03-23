"""Tests for the caching layer (MethodCache and AsyncTickerScopeClient integration)."""

from __future__ import annotations

import inspect

import httpx
import respx
from unittest.mock import patch

from tickerscope._auth import GRAPHQL_URL
from tickerscope._cache import MethodCache
from tickerscope._client import AsyncTickerScopeClient

FAKE_JWT = "fake_cache_test_jwt"


# ---------------------------------------------------------------------------
# Unit tests: MethodCache.build_key()
# ---------------------------------------------------------------------------


class TestBuildKey:
    """Tests for MethodCache.build_key() determinism and uniqueness."""

    def test_deterministic_same_args(self):
        """Identical arguments produce identical keys."""
        key1 = MethodCache.build_key("get_stock", "AAPL")
        key2 = MethodCache.build_key("get_stock", "AAPL")
        assert key1 == key2

    def test_different_positional_args_produce_different_keys(self):
        """Different positional arguments produce different keys."""
        key_aapl = MethodCache.build_key("get_stock", "AAPL")
        key_msft = MethodCache.build_key("get_stock", "MSFT")
        assert key_aapl != key_msft

    def test_different_method_names_produce_different_keys(self):
        """Different method names produce different keys even with same args."""
        key_stock = MethodCache.build_key("get_stock", "AAPL")
        key_ownership = MethodCache.build_key("get_ownership", "AAPL")
        assert key_stock != key_ownership

    def test_different_kwargs_produce_different_keys(self):
        """Different keyword arguments produce different keys."""
        key1 = MethodCache.build_key("get_chart_data", "AAPL", period="P1D")
        key2 = MethodCache.build_key("get_chart_data", "AAPL", period="P1W")
        assert key1 != key2

    def test_kwarg_order_does_not_matter(self):
        """Keyword argument order does not affect the key (sorted internally)."""
        key1 = MethodCache.build_key("method", a="1", b="2")
        key2 = MethodCache.build_key("method", b="2", a="1")
        assert key1 == key2

    def test_no_args_produces_consistent_key(self):
        """No arguments produces a consistent key across calls."""
        key1 = MethodCache.build_key("get_watchlist_names")
        key2 = MethodCache.build_key("get_watchlist_names")
        assert key1 == key2


# ---------------------------------------------------------------------------
# Unit tests: MethodCache.get() / set() round-trip
# ---------------------------------------------------------------------------


class TestGetSetRoundTrip:
    """Tests for MethodCache.get() and set() methods."""

    async def test_get_returns_none_on_miss(self):
        """Cache miss returns None."""
        cache = MethodCache(ttl=60)
        result = await cache.get("nonexistent_key")
        assert result is None

    async def test_set_then_get_returns_value(self):
        """Setting a value and getting it back returns the stored value."""
        cache = MethodCache(ttl=60)
        await cache.set("test_key", {"symbol": "AAPL", "price": 150.0})
        result = await cache.get("test_key")
        assert result == {"symbol": "AAPL", "price": 150.0}

    async def test_set_overwrites_existing_value(self):
        """Setting a key that already exists overwrites the old value."""
        cache = MethodCache(ttl=60)
        await cache.set("key", "old_value")
        await cache.set("key", "new_value")
        result = await cache.get("key")
        assert result == "new_value"

    async def test_different_keys_store_independently(self):
        """Different keys store and retrieve independently."""
        cache = MethodCache(ttl=60)
        await cache.set("key_a", "value_a")
        await cache.set("key_b", "value_b")
        assert await cache.get("key_a") == "value_a"
        assert await cache.get("key_b") == "value_b"


# ---------------------------------------------------------------------------
# Unit tests: MethodCache.clear()
# ---------------------------------------------------------------------------


class TestClear:
    """Tests for MethodCache.clear() method."""

    async def test_clear_removes_all_entries(self):
        """Clearing the cache removes all previously stored entries."""
        cache = MethodCache(ttl=60)
        await cache.set("key1", "val1")
        await cache.set("key2", "val2")
        await cache.clear()
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    async def test_clear_on_empty_cache_is_safe(self):
        """Clearing an empty cache raises no errors."""
        cache = MethodCache(ttl=60)
        await cache.clear()  # should not raise


# ---------------------------------------------------------------------------
# Integration tests: AsyncTickerScopeClient caching behavior
# ---------------------------------------------------------------------------


class TestCacheTtlZeroDisablesCache:
    """Verify that cache_ttl=0 (default) means no cache is allocated."""

    def test_default_cache_ttl_produces_no_cache(self):
        """Default cache_ttl=0 results in _cache being None."""
        with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
            client = AsyncTickerScopeClient()
        assert client._cache is None

    def test_explicit_zero_cache_ttl_produces_no_cache(self):
        """Explicit cache_ttl=0 results in _cache being None."""
        with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
            client = AsyncTickerScopeClient(cache_ttl=0)
        assert client._cache is None

    def test_positive_cache_ttl_creates_cache(self):
        """Positive cache_ttl results in a MethodCache instance."""
        with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
            client = AsyncTickerScopeClient(cache_ttl=60)
        assert client._cache is not None
        assert isinstance(client._cache, MethodCache)


class TestCacheHitSkipsHttp:
    """Verify that the second call returns cached result without HTTP."""

    @respx.mock
    async def test_second_call_uses_cache(self, stock_response):
        """Second get_stock call hits cache instead of the network."""
        with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
            client = AsyncTickerScopeClient(cache_ttl=60)

        route = respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=stock_response)
        )

        result1 = await client.get_stock("TEST")
        result2 = await client.get_stock("TEST")

        assert result1.symbol == "TEST"
        assert result2.symbol == "TEST"
        assert route.call_count == 1  # second call came from cache

        await client.aclose()


class TestUseCacheFalse:
    """Verify that use_cache=False bypasses the cache."""

    @respx.mock
    async def test_use_cache_false_makes_http_request(self, stock_response):
        """Calling with use_cache=False always hits the network."""
        with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
            client = AsyncTickerScopeClient(cache_ttl=60)

        route = respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=stock_response)
        )

        await client.get_stock("TEST")  # populates cache
        await client.get_stock("TEST", use_cache=False)  # bypasses cache

        assert route.call_count == 2

        await client.aclose()


class TestClearCacheForcesFetch:
    """Verify that clear_cache() causes the next call to hit the network."""

    @respx.mock
    async def test_clear_cache_invalidates_entries(self, stock_response):
        """After clear_cache(), the next call makes an HTTP request."""
        with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
            client = AsyncTickerScopeClient(cache_ttl=60)

        route = respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=stock_response)
        )

        await client.get_stock("TEST")  # populates cache
        assert route.call_count == 1

        await client.clear_cache()

        await client.get_stock("TEST")  # cache cleared, hits network
        assert route.call_count == 2

        await client.aclose()


class TestNonCacheableMethods:
    """Verify non-cacheable methods do NOT accept use_cache parameter."""

    def test_run_screen_has_no_use_cache(self):
        """run_screen does not accept a use_cache parameter."""
        sig = inspect.signature(AsyncTickerScopeClient.run_screen)
        assert "use_cache" not in sig.parameters

    def test_get_triggered_alerts_has_no_use_cache(self):
        """get_triggered_alerts does not accept a use_cache parameter."""
        sig = inspect.signature(AsyncTickerScopeClient.get_triggered_alerts)
        assert "use_cache" not in sig.parameters

    def test_get_watchlist_has_no_use_cache(self):
        """get_watchlist does not accept a use_cache parameter."""
        sig = inspect.signature(AsyncTickerScopeClient.get_watchlist)
        assert "use_cache" not in sig.parameters
