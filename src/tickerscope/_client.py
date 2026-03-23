"""Sync and async MarketSurge API clients."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any, Awaitable, Callable

import httpx

from tickerscope._cache import MethodCache
from tickerscope._auth import (
    DYLAN_TOKEN,
    GRAPHQL_URL,
    USER_AGENT,
    authenticate,  # noqa: F401 -- kept for backward-compat test patching
    async_resolve_jwt,
    is_token_expired as _is_token_expired,
    resolve_jwt,
)
from tickerscope._exceptions import APIError, AuthenticationError, TokenExpiredError
from tickerscope._models import (
    AlertSubscriptionList,
    ChartData,
    ChartMarkupList,
    FundamentalData,
    Layout,
    OwnershipData,
    Screen,
    ScreenResult,
    StockData,
    TriggeredAlertList,
    WatchlistDetail,
    WatchlistEntry,
    WatchlistSummary,
)
from tickerscope._parsing import (
    parse_active_alerts_response,
    parse_chart_data_response,
    parse_chart_markups_response,
    parse_fundamentals_response,
    parse_layouts_response,
    parse_ownership_response,
    parse_screen_result_response,
    parse_screens_response,
    parse_stock_response,
    parse_triggered_alerts_response,
    parse_watchlist_detail_response,
    parse_watchlist_names_response,
    parse_watchlist_response,
)
from tickerscope._queries import (
    ACTIVE_ALERTS_QUERY,
    ADHOC_SCREEN_QUERY,
    CHART_MARKET_DATA_QUERY,
    CHART_MARKUPS_QUERY,
    FLAGGED_SYMBOLS_QUERY,
    FUNDAMENTALS_QUERY,
    MARKET_DATA_LAYOUTS_QUERY,
    MARKET_DATA_SCREEN_QUERY,
    OTHER_MARKET_DATA_QUERY,
    OWNERSHIP_QUERY,
    SCREENS_QUERY,
    TRIGGERED_ALERTS_QUERY,
    WATCHLIST_COLUMNS,
    WATCHLIST_NAMES_QUERY,
)

_log = logging.getLogger("tickerscope")


def _apply_max_points(chart: ChartData, max_points: int | None) -> ChartData:
    """Truncate chart data points to max_points if specified."""
    if max_points is None:
        return chart
    if max_points < 0:
        raise ValueError("max_points must be non-negative")
    if chart.time_series is not None:
        return replace(
            chart,
            time_series=replace(
                chart.time_series,
                data_points=chart.time_series.data_points[:max_points],
            ),
        )
    return chart


class BaseTickerScopeClient(ABC):
    """Shared behavior for sync and async TickerScope clients."""

    _jwt: str

    @staticmethod
    def _build_headers(jwt: str) -> dict[str, str]:
        return {
            "User-Agent": USER_AGENT,
            "content-type": "application/json",
            "authorization": f"Bearer {jwt}",
            "apollographql-client-name": "marketsurge",
            "dylan-entitlement-token": DYLAN_TOKEN,
            "Referer": "https://marketsurge-beta.investors.com/",
            "Origin": "https://marketsurge-beta.investors.com",
        }

    @property
    def is_token_expired(self) -> bool:
        """Check whether the stored JWT token has expired."""
        return _is_token_expired(self._jwt)

    @classmethod
    def capabilities(cls) -> dict[str, Any]:
        """Return metadata about available client methods and API capabilities.

        Returns a JSON-serializable dict describing all methods, their parameters,
        return types, and caching/pagination support. Can be called without
        instantiating a client (no authentication required).

        Returns:
            Dict with keys: auth_required, api_endpoint, async_only_caching, methods.
        """
        return {
            "auth_required": True,
            "api_endpoint": GRAPHQL_URL,
            "async_only_caching": True,
            "methods": [
                {
                    "name": "get_stock",
                    "return_type": "StockData",
                    "cacheable": True,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                        {
                            "name": "symbol_dialect_type",
                            "type": "str",
                            "required": False,
                            "default": "CHARTING",
                        },
                    ],
                },
                {
                    "name": "get_chart_data",
                    "return_type": "ChartData",
                    "cacheable": True,
                    "supports_limit": False,
                    "supports_max_points": True,
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                        {"name": "start_date", "type": "str", "required": True},
                        {"name": "end_date", "type": "str", "required": True},
                        {
                            "name": "period",
                            "type": "str",
                            "required": False,
                            "default": "P1D",
                        },
                        {
                            "name": "exchange",
                            "type": "str",
                            "required": False,
                            "default": "NYSE",
                        },
                    ],
                },
                {
                    "name": "get_watchlist",
                    "return_type": "list[WatchlistEntry]",
                    "cacheable": False,
                    "supports_limit": True,
                    "parameters": [
                        {"name": "list_id", "type": "int", "required": True},
                    ],
                },
                {
                    "name": "get_ownership",
                    "return_type": "OwnershipData",
                    "cacheable": True,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_watchlist_names",
                    "return_type": "list[WatchlistSummary]",
                    "cacheable": True,
                    "supports_limit": True,
                    "parameters": [],
                },
                {
                    "name": "get_watchlist_items",
                    "return_type": "WatchlistDetail",
                    "cacheable": True,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "watchlist_id", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_screens",
                    "return_type": "list[Screen]",
                    "cacheable": True,
                    "supports_limit": True,
                    "parameters": [
                        {
                            "name": "screen_type",
                            "type": "str | None",
                            "required": False,
                            "default": None,
                        },
                        {
                            "name": "sort_dir",
                            "type": "str | None",
                            "required": False,
                            "default": None,
                        },
                    ],
                },
                {
                    "name": "run_screen",
                    "return_type": "ScreenResult",
                    "cacheable": False,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "screen_name", "type": "str", "required": True},
                        {
                            "name": "parameters",
                            "type": "list[dict[str, str]]",
                            "required": True,
                        },
                    ],
                },
                {
                    "name": "get_fundamentals",
                    "return_type": "FundamentalData",
                    "cacheable": True,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_active_alerts",
                    "return_type": "AlertSubscriptionList",
                    "cacheable": True,
                    "supports_limit": True,
                    "parameters": [],
                },
                {
                    "name": "get_triggered_alerts",
                    "return_type": "TriggeredAlertList",
                    "cacheable": False,
                    "supports_limit": True,
                    "parameters": [],
                },
                {
                    "name": "get_layouts",
                    "return_type": "list[Layout]",
                    "cacheable": True,
                    "supports_limit": True,
                    "parameters": [],
                },
                {
                    "name": "get_chart_markups",
                    "return_type": "ChartMarkupList",
                    "cacheable": True,
                    "supports_limit": True,
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                        {
                            "name": "frequency",
                            "type": "str",
                            "required": False,
                            "default": "DAILY",
                        },
                        {
                            "name": "sort_dir",
                            "type": "str",
                            "required": False,
                            "default": "ASC",
                        },
                    ],
                },
                {
                    "name": "get_watchlist_by_name",
                    "return_type": "WatchlistDetail",
                    "cacheable": True,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "name", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_screen_by_name",
                    "return_type": "Screen",
                    "cacheable": True,
                    "supports_limit": False,
                    "parameters": [
                        {"name": "name", "type": "str", "required": True},
                    ],
                },
            ],
        }

    @abstractmethod
    def _graphql(
        self, payload: dict[str, Any]
    ) -> dict[str, Any] | Awaitable[dict[str, Any]]:
        """Execute GraphQL request and return response data."""

    @staticmethod
    def _build_get_stock_payload(
        symbol: str, symbol_dialect_type: str = "CHARTING"
    ) -> dict[str, Any]:
        return {
            "operationName": "OtherMarketData",
            "variables": {
                "symbols": [symbol],
                "symbolDialectType": symbol_dialect_type,
                "upToHistoricalPeriodForProfitMargin": "P12Q_AGO",
                "upToHistoricalPeriodOffset": "P24Q_AGO",
                "upToQueryPeriodOffset": "P4Q_FUTURE",
            },
            "query": OTHER_MARKET_DATA_QUERY,
        }

    @staticmethod
    def _build_get_chart_data_payload(
        symbol: str,
        *,
        start_date: str,
        end_date: str,
        period: str = "P1D",
        exchange: str = "NYSE",
    ) -> dict[str, Any]:
        return {
            "operationName": "ChartMarketData",
            "variables": {
                "symbols": [symbol],
                "symbolDialectType": "CHARTING",
                "where": {
                    "startDateTime": {"eq": start_date},
                    "endDateTime": {"eq": end_date},
                    "timeSeriesType": {"eq": period},
                    "includeIntradayData": True,
                },
                "exchangeName": exchange,
            },
            "query": CHART_MARKET_DATA_QUERY,
        }

    @staticmethod
    def _build_get_watchlist_payload(list_id: int) -> dict[str, Any]:
        return {
            "operationName": "MarketDataAdhocScreen",
            "variables": {
                "correlationTag": "marketsurge",
                "responseColumns": WATCHLIST_COLUMNS,
                "adhocQuery": None,
                "includeSource": {
                    "screenId": {"id": list_id, "dialect": "MS_LIST_ID"},
                },
                "pageSize": 1000,
                "resultLimit": 1000000,
                "pageSkip": 0,
                "resultType": "RESULT_WITH_EXPRESSION_COUNTS",
            },
            "query": ADHOC_SCREEN_QUERY,
        }

    @staticmethod
    def _build_get_ownership_payload(symbol: str) -> dict[str, Any]:
        return {
            "operationName": "Ownership",
            "variables": {
                "symbols": [symbol],
                "symbolDialectType": "CHARTING",
            },
            "query": OWNERSHIP_QUERY,
        }

    @staticmethod
    def _build_get_watchlist_names_payload() -> dict[str, Any]:
        return {
            "operationName": "GetAllWatchlistNames",
            "variables": {"pub": "msr"},
            "query": WATCHLIST_NAMES_QUERY,
        }

    @staticmethod
    def _build_get_watchlist_items_payload(watchlist_id: str) -> dict[str, Any]:
        return {
            "operationName": "FlaggedSymbols",
            "variables": {"pub": "msr", "watchlistId": watchlist_id},
            "query": FLAGGED_SYMBOLS_QUERY,
        }

    @staticmethod
    def _build_get_screens_payload(
        screen_type: str | None = None,
        sort_dir: str | None = None,
    ) -> dict[str, Any]:
        variables: dict[str, str] = {"site": "marketsurge"}
        if screen_type is not None:
            variables["type"] = screen_type
        if sort_dir is not None:
            variables["sortDir"] = sort_dir
        return {
            "operationName": "Screens",
            "variables": variables,
            "query": SCREENS_QUERY,
        }

    @staticmethod
    def _build_run_screen_payload(
        screen_name: str,
        parameters: list[dict[str, str]],
    ) -> dict[str, Any]:
        return {
            "operationName": "MarketDataScreen",
            "variables": {"screenName": screen_name, "parameters": parameters},
            "query": MARKET_DATA_SCREEN_QUERY,
        }

    @staticmethod
    def _build_get_fundamentals_payload(symbol: str) -> dict[str, Any]:
        return {
            "operationName": "FundermentalDataBox",
            "variables": {
                "symbols": [symbol],
                "symbolDialectType": "CHARTING",
                "upToHistoricalPeriodOffset": "P7Y_AGO",
                "upToQueryPeriodOffset": "P2Y_FUTURE",
                "reportedSalesUpToHistoricalPeriod2": "P7Y_AGO",
                "salesEstimatesUpToQueryPeriod2": "P2Y_FUTURE",
            },
            "query": FUNDAMENTALS_QUERY,
        }

    @staticmethod
    def _build_get_active_alerts_payload() -> dict[str, Any]:
        return {
            "operationName": "ActiveAlerts",
            "variables": {"product": "MARKETSURGE"},
            "query": ACTIVE_ALERTS_QUERY,
        }

    @staticmethod
    def _build_get_triggered_alerts_payload() -> dict[str, Any]:
        return {
            "operationName": "TriggeredAlerts",
            "variables": {},
            "query": TRIGGERED_ALERTS_QUERY,
        }

    @staticmethod
    def _build_get_layouts_payload() -> dict[str, Any]:
        return {
            "operationName": "MarketDataLayouts",
            "variables": {"site": "marketsurge"},
            "query": MARKET_DATA_LAYOUTS_QUERY,
        }

    @staticmethod
    def _build_get_chart_markups_payload(
        symbol: str, *, frequency: str = "DAILY", sort_dir: str = "ASC"
    ) -> dict[str, Any]:
        return {
            "operationName": "FetchChartMarkups",
            "variables": {
                "site": "marketsurge",
                "dowJonesKey": symbol,
                "frequency": frequency,
                "sortDir": sort_dir,
            },
            "query": CHART_MARKUPS_QUERY,
        }

    def _graphql_and_parse(
        self,
        payload: dict[str, Any],
        parse_fn: Callable[..., Any],
        *args: Any,
    ) -> Any:
        raw = self._graphql(payload)
        return parse_fn(raw, *args)

    def get_stock(self, symbol: str, symbol_dialect_type: str = "CHARTING") -> Any:
        payload = self._build_get_stock_payload(symbol, symbol_dialect_type)
        return self._graphql_and_parse(payload, parse_stock_response, symbol)

    def get_chart_data(
        self,
        symbol: str,
        *,
        start_date: str,
        end_date: str,
        period: str = "P1D",
        exchange: str = "NYSE",
        max_points: int | None = None,
    ) -> Any:
        payload = self._build_get_chart_data_payload(
            symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            exchange=exchange,
        )
        result = self._graphql_and_parse(payload, parse_chart_data_response, symbol)
        return _apply_max_points(result, max_points)

    def get_watchlist(self, list_id: int, *, limit: int | None = None) -> Any:
        payload = self._build_get_watchlist_payload(list_id)
        result = self._graphql_and_parse(payload, parse_watchlist_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    def get_ownership(self, symbol: str) -> Any:
        payload = self._build_get_ownership_payload(symbol)
        return self._graphql_and_parse(payload, parse_ownership_response, symbol)

    def get_watchlist_names(self, *, limit: int | None = None) -> Any:
        payload = self._build_get_watchlist_names_payload()
        result = self._graphql_and_parse(payload, parse_watchlist_names_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    def get_watchlist_items(self, watchlist_id: str) -> Any:
        payload = self._build_get_watchlist_items_payload(watchlist_id)
        return self._graphql_and_parse(
            payload, parse_watchlist_detail_response, watchlist_id
        )

    def get_screens(
        self,
        screen_type: str | None = None,
        sort_dir: str | None = None,
        *,
        limit: int | None = None,
    ) -> Any:
        payload = self._build_get_screens_payload(
            screen_type=screen_type, sort_dir=sort_dir
        )
        result = self._graphql_and_parse(payload, parse_screens_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    def run_screen(
        self,
        screen_name: str,
        parameters: list[dict[str, str]],
    ) -> Any:
        payload = self._build_run_screen_payload(screen_name, parameters)
        return self._graphql_and_parse(payload, parse_screen_result_response)

    def get_fundamentals(self, symbol: str) -> Any:
        payload = self._build_get_fundamentals_payload(symbol)
        return self._graphql_and_parse(payload, parse_fundamentals_response, symbol)

    def get_active_alerts(self, *, limit: int | None = None) -> Any:
        payload = self._build_get_active_alerts_payload()
        result = self._graphql_and_parse(payload, parse_active_alerts_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = replace(result, subscriptions=result.subscriptions[:limit])
        return result

    def get_triggered_alerts(self, *, limit: int | None = None) -> Any:
        payload = self._build_get_triggered_alerts_payload()
        result = self._graphql_and_parse(payload, parse_triggered_alerts_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = replace(result, alerts=result.alerts[:limit])
        return result

    def get_layouts(self, *, limit: int | None = None) -> Any:
        payload = self._build_get_layouts_payload()
        result = self._graphql_and_parse(payload, parse_layouts_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    def get_chart_markups(
        self,
        symbol: str,
        *,
        frequency: str = "DAILY",
        sort_dir: str = "ASC",
        limit: int | None = None,
    ) -> Any:
        payload = self._build_get_chart_markups_payload(
            symbol,
            frequency=frequency,
            sort_dir=sort_dir,
        )
        result = self._graphql_and_parse(payload, parse_chart_markups_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = replace(result, markups=result.markups[:limit])
        return result


class TickerScopeClient(BaseTickerScopeClient):
    """Authenticated sync client for the MarketSurge GraphQL API."""

    def __init__(
        self, browser: str = "firefox", timeout: float = 30.0, *, jwt: str | None = None
    ) -> None:
        self._jwt = resolve_jwt(jwt=jwt, browser=browser, timeout=timeout)
        self._http = httpx.Client(headers=self._build_headers(self._jwt))

    def __enter__(self) -> TickerScopeClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _graphql(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = self._http.post(GRAPHQL_URL, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise TokenExpiredError(
                    "JWT token has expired or is invalid (HTTP 401)",
                    status_code=401,
                ) from exc
            if exc.response.status_code == 403:
                raise AuthenticationError(
                    "Access denied -- token may lack required permissions (HTTP 403)",
                ) from exc
            raise
        return resp.json()

    def get_watchlist_by_name(self, name: str) -> WatchlistDetail:
        """Look up a watchlist by name and return its full details.

        Calls get_watchlist_names() to find the matching watchlist,
        then get_watchlist_items() to fetch all entries.

        Args:
            name: The exact name of the watchlist to look up.

        Returns:
            WatchlistDetail with all items in the named watchlist.

        Raises:
            APIError: If no watchlist matches the given name, or if the
                watchlist has no ID.
        """
        summaries = self.get_watchlist_names()
        match = next((w for w in summaries if w.name == name), None)
        if match is None:
            raise APIError(f"No watchlist found with name {name!r}")
        if match.id is None:
            raise APIError(f"Watchlist {name!r} has no ID")
        return self.get_watchlist_items(match.id)

    def get_screen_by_name(self, name: str) -> Screen:
        """Look up a saved screen by name and return its metadata.

        Calls get_screens() and returns the first Screen matching the name.

        Note: This returns user-saved screen metadata. The returned Screen
        object cannot be directly passed to run_screen(), which requires
        fully-qualified predefined screen names.

        Args:
            name: The exact name of the screen to look up.

        Returns:
            The matching Screen object.

        Raises:
            APIError: If no screen matches the given name.
        """
        screens = self.get_screens()
        match = next((s for s in screens if s.name == name), None)
        if match is None:
            raise APIError(f"No screen found with name {name!r}")
        return match


class AsyncTickerScopeClient(BaseTickerScopeClient):
    """Authenticated async client for the MarketSurge GraphQL API."""

    def __init__(
        self,
        browser: str = "firefox",
        timeout: float = 30.0,
        *,
        jwt: str | None = None,
        cache_ttl: int = 0,
    ) -> None:
        self._jwt = resolve_jwt(jwt=jwt, browser=browser, timeout=timeout)
        self._http = httpx.AsyncClient(headers=self._build_headers(self._jwt))
        self._cache: MethodCache | None = (
            MethodCache(ttl=cache_ttl) if cache_ttl > 0 else None
        )

    async def __aenter__(self) -> AsyncTickerScopeClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    @classmethod
    async def create(
        cls,
        browser: str = "firefox",
        timeout: float = 30.0,
        *,
        jwt: str | None = None,
        cache_ttl: int = 0,
    ) -> "AsyncTickerScopeClient":
        instance = object.__new__(cls)
        instance._jwt = await async_resolve_jwt(
            jwt=jwt, browser=browser, timeout=timeout
        )
        instance._http = httpx.AsyncClient(
            headers=instance._build_headers(instance._jwt)
        )
        instance._cache = MethodCache(ttl=cache_ttl) if cache_ttl > 0 else None
        return instance

    async def aclose(self) -> None:
        await self._http.aclose()

    async def clear_cache(self) -> None:
        """Clear all cached method results.

        Safe to call even when caching is disabled (cache_ttl=0).
        """
        if self._cache is not None:
            await self._cache.clear()

    async def _graphql(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = await self._http.post(GRAPHQL_URL, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                await self.clear_cache()
                raise TokenExpiredError(
                    "JWT token has expired or is invalid (HTTP 401)",
                    status_code=401,
                ) from exc
            if exc.response.status_code == 403:
                raise AuthenticationError(
                    "Access denied -- token may lack required permissions (HTTP 403)",
                ) from exc
            raise
        return resp.json()

    async def _graphql_and_parse(
        self,
        payload: dict[str, Any],
        parse_fn: Callable[..., Any],
        *args: Any,
    ) -> Any:
        raw = await self._graphql(payload)
        return parse_fn(raw, *args)

    async def get_stock(
        self,
        symbol: str,
        symbol_dialect_type: str = "CHARTING",
        *,
        use_cache: bool = True,
    ) -> StockData:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_stock", symbol, symbol_dialect_type)
            cached = await self._cache.get(key)
            if cached is not None:
                return cached
        payload = self._build_get_stock_payload(symbol, symbol_dialect_type)
        result = await self._graphql_and_parse(payload, parse_stock_response, symbol)
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_stock", symbol, symbol_dialect_type)
            await self._cache.set(key, result)
        return result

    async def get_chart_data(
        self,
        symbol: str,
        *,
        start_date: str,
        end_date: str,
        period: str = "P1D",
        exchange: str = "NYSE",
        max_points: int | None = None,
        use_cache: bool = True,
    ) -> ChartData:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key(
                "get_chart_data",
                symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                exchange=exchange,
            )
            cached = await self._cache.get(key)
            if cached is not None:
                return _apply_max_points(cached, max_points)
        payload = self._build_get_chart_data_payload(
            symbol,
            start_date=start_date,
            end_date=end_date,
            period=period,
            exchange=exchange,
        )
        result = await self._graphql_and_parse(
            payload, parse_chart_data_response, symbol
        )
        if self._cache is not None and use_cache:
            key = MethodCache.build_key(
                "get_chart_data",
                symbol,
                start_date=start_date,
                end_date=end_date,
                period=period,
                exchange=exchange,
            )
            await self._cache.set(key, result)
        return _apply_max_points(result, max_points)

    async def get_watchlist(
        self, list_id: int, *, limit: int | None = None
    ) -> list[WatchlistEntry]:
        payload = self._build_get_watchlist_payload(list_id)
        result = await self._graphql_and_parse(payload, parse_watchlist_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    async def get_ownership(
        self, symbol: str, *, use_cache: bool = True
    ) -> OwnershipData:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_ownership", symbol)
            cached = await self._cache.get(key)
            if cached is not None:
                return cached
        payload = self._build_get_ownership_payload(symbol)
        result = await self._graphql_and_parse(
            payload, parse_ownership_response, symbol
        )
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_ownership", symbol)
            await self._cache.set(key, result)
        return result

    async def get_watchlist_names(
        self, *, limit: int | None = None, use_cache: bool = True
    ) -> list[WatchlistSummary]:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_watchlist_names")
            cached = await self._cache.get(key)
            if cached is not None:
                if limit is not None:
                    if limit < 0:
                        raise ValueError("limit must be non-negative")
                    cached = cached[:limit]
                return cached
        payload = self._build_get_watchlist_names_payload()
        result = await self._graphql_and_parse(payload, parse_watchlist_names_response)
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_watchlist_names")
            await self._cache.set(key, result)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    async def get_watchlist_items(
        self, watchlist_id: str, *, use_cache: bool = True
    ) -> WatchlistDetail:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_watchlist_items", watchlist_id)
            cached = await self._cache.get(key)
            if cached is not None:
                return cached
        payload = self._build_get_watchlist_items_payload(watchlist_id)
        result = await self._graphql_and_parse(
            payload,
            parse_watchlist_detail_response,
            watchlist_id,
        )
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_watchlist_items", watchlist_id)
            await self._cache.set(key, result)
        return result

    async def get_screens(
        self,
        screen_type: str | None = None,
        sort_dir: str | None = None,
        *,
        limit: int | None = None,
        use_cache: bool = True,
    ) -> list[Screen]:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key(
                "get_screens", screen_type=screen_type, sort_dir=sort_dir
            )
            cached = await self._cache.get(key)
            if cached is not None:
                if limit is not None:
                    if limit < 0:
                        raise ValueError("limit must be non-negative")
                    cached = cached[:limit]
                return cached
        payload = self._build_get_screens_payload(
            screen_type=screen_type, sort_dir=sort_dir
        )
        result = await self._graphql_and_parse(payload, parse_screens_response)
        if self._cache is not None and use_cache:
            key = MethodCache.build_key(
                "get_screens", screen_type=screen_type, sort_dir=sort_dir
            )
            await self._cache.set(key, result)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    async def run_screen(
        self,
        screen_name: str,
        parameters: list[dict[str, str]],
    ) -> ScreenResult:
        payload = self._build_run_screen_payload(screen_name, parameters)
        return await self._graphql_and_parse(payload, parse_screen_result_response)

    async def get_fundamentals(
        self, symbol: str, *, use_cache: bool = True
    ) -> FundamentalData:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_fundamentals", symbol)
            cached = await self._cache.get(key)
            if cached is not None:
                return cached
        payload = self._build_get_fundamentals_payload(symbol)
        result = await self._graphql_and_parse(
            payload, parse_fundamentals_response, symbol
        )
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_fundamentals", symbol)
            await self._cache.set(key, result)
        return result

    async def get_active_alerts(
        self, *, limit: int | None = None, use_cache: bool = True
    ) -> AlertSubscriptionList:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_active_alerts")
            cached = await self._cache.get(key)
            if cached is not None:
                if limit is not None:
                    if limit < 0:
                        raise ValueError("limit must be non-negative")
                    cached = replace(cached, subscriptions=cached.subscriptions[:limit])
                return cached
        payload = self._build_get_active_alerts_payload()
        result = await self._graphql_and_parse(payload, parse_active_alerts_response)
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_active_alerts")
            await self._cache.set(key, result)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = replace(result, subscriptions=result.subscriptions[:limit])
        return result

    async def get_triggered_alerts(
        self, *, limit: int | None = None
    ) -> TriggeredAlertList:
        payload = self._build_get_triggered_alerts_payload()
        result = await self._graphql_and_parse(payload, parse_triggered_alerts_response)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = replace(result, alerts=result.alerts[:limit])
        return result

    async def get_layouts(
        self, *, limit: int | None = None, use_cache: bool = True
    ) -> list[Layout]:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_layouts")
            cached = await self._cache.get(key)
            if cached is not None:
                if limit is not None:
                    if limit < 0:
                        raise ValueError("limit must be non-negative")
                    cached = cached[:limit]
                return cached
        payload = self._build_get_layouts_payload()
        result = await self._graphql_and_parse(payload, parse_layouts_response)
        if self._cache is not None and use_cache:
            key = MethodCache.build_key("get_layouts")
            await self._cache.set(key, result)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = result[:limit]
        return result

    async def get_chart_markups(
        self,
        symbol: str,
        *,
        frequency: str = "DAILY",
        sort_dir: str = "ASC",
        limit: int | None = None,
        use_cache: bool = True,
    ) -> ChartMarkupList:
        if self._cache is not None and use_cache:
            key = MethodCache.build_key(
                "get_chart_markups",
                symbol,
                frequency=frequency,
                sort_dir=sort_dir,
            )
            cached = await self._cache.get(key)
            if cached is not None:
                if limit is not None:
                    if limit < 0:
                        raise ValueError("limit must be non-negative")
                    cached = replace(cached, markups=cached.markups[:limit])
                return cached
        payload = self._build_get_chart_markups_payload(
            symbol,
            frequency=frequency,
            sort_dir=sort_dir,
        )
        result = await self._graphql_and_parse(payload, parse_chart_markups_response)
        if self._cache is not None and use_cache:
            key = MethodCache.build_key(
                "get_chart_markups",
                symbol,
                frequency=frequency,
                sort_dir=sort_dir,
            )
            await self._cache.set(key, result)
        if limit is not None:
            if limit < 0:
                raise ValueError("limit must be non-negative")
            result = replace(result, markups=result.markups[:limit])
        return result

    async def get_watchlist_by_name(self, name: str) -> WatchlistDetail:
        """Look up a watchlist by name and return its full details.

        Calls get_watchlist_names() to find the matching watchlist,
        then get_watchlist_items() to fetch all entries.

        Args:
            name: The exact name of the watchlist to look up.

        Returns:
            WatchlistDetail with all items in the named watchlist.

        Raises:
            APIError: If no watchlist matches the given name, or if the
                watchlist has no ID.
        """
        summaries = await self.get_watchlist_names()
        match = next((w for w in summaries if w.name == name), None)
        if match is None:
            raise APIError(f"No watchlist found with name {name!r}")
        if match.id is None:
            raise APIError(f"Watchlist {name!r} has no ID")
        return await self.get_watchlist_items(match.id)

    async def get_screen_by_name(self, name: str) -> Screen:
        """Look up a saved screen by name and return its metadata.

        Calls get_screens() and returns the first Screen matching the name.

        Note: This returns user-saved screen metadata. The returned Screen
        object cannot be directly passed to run_screen(), which requires
        fully-qualified predefined screen names.

        Args:
            name: The exact name of the screen to look up.

        Returns:
            The matching Screen object.

        Raises:
            APIError: If no screen matches the given name.
        """
        screens = await self.get_screens()
        match = next((s for s in screens if s.name == name), None)
        if match is None:
            raise APIError(f"No screen found with name {name!r}")
        return match
