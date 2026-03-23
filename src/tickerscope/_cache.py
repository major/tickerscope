"""Optional caching helpers for async TickerScope client methods."""

from __future__ import annotations

from typing import Any


class MethodCache:
    """Optional in-memory TTL cache wrapping aiocache.SimpleMemoryCache."""

    def __init__(self, ttl: int) -> None:
        """Initialize cache backend with a fixed TTL in seconds.

        Args:
            ttl: Time-to-live for all cache entries, in seconds.

        Raises:
            ImportError: If aiocache is not installed.
        """
        try:
            from aiocache import SimpleMemoryCache  # pyright: ignore[reportMissingImports]
        except ImportError as exc:
            raise ImportError(
                "aiocache is required for caching. Install with: "
                "pip install tickerscope[cache]"
            ) from exc

        self._cache = SimpleMemoryCache()
        self.ttl = ttl

    async def get(self, key: str) -> Any | None:
        """Return cached value for key, or None on cache miss."""
        return await self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Store value under key using the instance TTL."""
        await self._cache.set(key, value, ttl=self.ttl)

    async def clear(self) -> None:
        """Clear all cached entries from the backend."""
        await self._cache.clear()

    @staticmethod
    def build_key(method_name: str, *args: Any, **kwargs: Any) -> str:
        """Build a deterministic cache key from method name and arguments."""
        return f"{method_name}:{args!r}:{tuple(sorted(kwargs.items()))!r}"
