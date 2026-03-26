"""Sync and async MarketSurge API clients."""

from __future__ import annotations

import asyncio
import datetime
import logging
from calendar import monthrange
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Any, Awaitable, Callable

import httpx

from tickerscope._auth import (
    DYLAN_TOKEN,
    GRAPHQL_URL,
    USER_AGENT,
    authenticate,  # noqa: F401 -- kept for backward-compat test patching
    async_resolve_jwt,
    is_token_expired as _is_token_expired,
    resolve_jwt,
)
from tickerscope._exceptions import (
    APIError,
    AuthenticationError,
    HTTPError,
    TokenExpiredError,
)
from tickerscope._models import (
    AdhocScreenResult,
    AlertSubscriptionList,
    CatalogEntry,
    ChartData,
    ChartMarkupList,
    CoachTreeData,
    FundamentalData,
    Layout,
    NavTreeFolder,
    NavTreeLeaf,
    NavTreeNode,
    OwnershipData,
    Panel,
    PREDEFINED_REPORTS,
    ReportInfo,
    RSRatingHistory,
    Screen,
    ScreenResult,
    StockAnalysis,
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
    parse_coach_tree_response,
    parse_fundamentals_response,
    parse_layouts_response,
    parse_nav_tree_response,
    parse_ownership_response,
    parse_panels_response,
    parse_rs_rating_history_response,
    parse_run_screen_response,
    parse_screen_result_response,
    parse_screens_response,
    parse_server_time_response,
    parse_stock_response,
    parse_triggered_alerts_response,
    parse_watchlist_detail_response,
    parse_watchlists_response,
    parse_watchlist_response,
)
from tickerscope._queries import (
    ACTIVE_ALERTS_QUERY,
    ADHOC_SCREEN_QUERY,
    ALL_PANELS_QUERY,
    CHART_MARKET_DATA_QUERY,
    CHART_MARKET_DATA_WEEKLY_QUERY,
    CHART_MARKUPS_QUERY,
    COACH_TREE_QUERY,
    FLAGGED_SYMBOLS_QUERY,
    FUNDAMENTALS_QUERY,
    GET_SERVER_DATE_TIME_QUERY,
    MARKET_DATA_LAYOUTS_QUERY,
    MARKET_DATA_SCREEN_QUERY,
    NAV_TREE_QUERY,
    RUN_SCREEN_QUERY,
    OTHER_MARKET_DATA_QUERY,
    OWNERSHIP_QUERY,
    RS_RATING_RI_PANEL_QUERY,
    SCREENS_QUERY,
    TRIGGERED_ALERTS_QUERY,
    WATCHLIST_COLUMNS,
    WATCHLIST_NAMES_QUERY,
)

_log = logging.getLogger("tickerscope")

_VALID_LOOKBACKS = ("1W", "1M", "3M", "6M", "1Y", "YTD")

_COACH_SCREEN_TYPES = ("STOCK_SCREEN", "FUND_SCREEN")


def _find_coach_screen(nodes: list[NavTreeNode], name: str) -> NavTreeLeaf | None:
    """Walk the coach tree and return the first leaf matching *name*."""
    for node in nodes:
        if isinstance(node, NavTreeLeaf):
            if node.node_type in _COACH_SCREEN_TYPES and node.name == name:
                return node
        elif isinstance(node, NavTreeFolder):
            found = _find_coach_screen(node.children, name)
            if found is not None:
                return found
    return None


def _list_coach_screen_names(nodes: list[NavTreeNode]) -> str:
    """Collect display names of all coach screen leaves, comma-separated."""
    names: list[str] = []

    def _collect(items: list[NavTreeNode]) -> None:
        for node in items:
            if isinstance(node, NavTreeLeaf):
                if node.node_type in _COACH_SCREEN_TYPES and node.name:
                    names.append(node.name)
            elif isinstance(node, NavTreeFolder):
                _collect(node.children)

    _collect(nodes)
    return ", ".join(sorted(set(names)))


def _extract_leaves(nodes: list[NavTreeNode]) -> list[NavTreeLeaf]:
    """Recursively extract all leaf nodes from a navigation tree."""
    leaves: list[NavTreeLeaf] = []
    for node in nodes:
        if isinstance(node, NavTreeLeaf):
            leaves.append(node)
        elif isinstance(node, NavTreeFolder):
            leaves.extend(_extract_leaves(node.children))
    return leaves


def _screens_to_catalog(screens: list[Screen]) -> list[CatalogEntry]:
    """Convert user screens to catalog entries (discovery-only, not dispatchable)."""
    return [
        CatalogEntry(
            name=screen.name,
            kind="screen",
            description=screen.description,
        )
        for screen in screens
        if screen.name is not None
    ]


def _reports_to_catalog(reports: list[ReportInfo]) -> list[CatalogEntry]:
    """Convert predefined reports to catalog entries."""
    return [
        CatalogEntry(
            name=report.name,
            kind="report",
            report_id=report.original_id,
        )
        for report in reports
    ]


def _coach_tree_to_catalog(tree: CoachTreeData) -> list[CatalogEntry]:
    """Extract catalog entries from the coach tree (screens and watchlists).

    Processes both the ``.screens`` and ``.watchlists`` sub-trees and
    returns a flat list of entries. Screen leaves are filtered to
    ``_COACH_SCREEN_TYPES`` node types with a non-None
    ``reference_screen_id``. Watchlist leaves must have a non-None
    ``reference_watchlist_id`` (stored as ``str``, converted to ``int``).
    """
    entries: list[CatalogEntry] = []

    for leaf in _extract_leaves(tree.screens):
        if leaf.node_type not in _COACH_SCREEN_TYPES:
            continue
        if leaf.reference_screen_id is None:
            continue
        entries.append(
            CatalogEntry(
                name=leaf.name or "",
                kind="coach_screen",
                coach_screen_id=leaf.reference_screen_id,
            )
        )

    for leaf in _extract_leaves(tree.watchlists):
        if leaf.reference_watchlist_id is None:
            continue
        try:
            watchlist_id = int(leaf.reference_watchlist_id)
        except (ValueError, TypeError):
            continue
        entries.append(
            CatalogEntry(
                name=leaf.name or "",
                kind="watchlist",
                watchlist_id=watchlist_id,
            )
        )

    return entries


def _watchlists_to_catalog(summaries: list[WatchlistSummary]) -> list[CatalogEntry]:
    """Convert user watchlist summaries to catalog entries, filtering None IDs."""
    return [
        CatalogEntry(
            name=summary.name or "",
            kind="watchlist",
            description=summary.description,
            watchlist_id=summary.id,
        )
        for summary in summaries
        if summary.id is not None
    ]


def _today() -> date:
    """Return the local calendar date."""
    return date.today()


def _subtract_months(current: date, months: int) -> date:
    """Subtract months from a date, clamping to month-end if needed."""
    total_month_index = (current.year * 12) + (current.month - 1) - months
    target_year = total_month_index // 12
    target_month = (total_month_index % 12) + 1
    try:
        return current.replace(year=target_year, month=target_month)
    except ValueError:
        last_day = monthrange(target_year, target_month)[1]
        return date(target_year, target_month, last_day)


def _resolve_chart_dates(
    *,
    start_date: str | None,
    end_date: str | None,
    lookback: str | None,
    today: date | None = None,
) -> tuple[str, str]:
    """Resolve chart date inputs to a concrete start and end date pair."""
    explicit_dates = _validate_chart_date_inputs(
        start_date=start_date,
        end_date=end_date,
        lookback=lookback,
    )
    if explicit_dates is not None:
        return explicit_dates

    assert lookback is not None
    current = today or _today()
    end = current.strftime("%Y-%m-%d")
    start = _resolve_lookback_start_date(current, lookback)
    return start.strftime("%Y-%m-%d"), end


def _validate_chart_date_inputs(
    *,
    start_date: str | None,
    end_date: str | None,
    lookback: str | None,
) -> tuple[str, str] | None:
    """Validate date inputs and return explicit dates when provided."""
    _raise_if_lookback_mixed_with_explicit_dates(
        start_date=start_date,
        end_date=end_date,
        lookback=lookback,
    )
    explicit_dates = _resolve_explicit_dates(
        start_date=start_date,
        end_date=end_date,
        lookback=lookback,
    )
    if explicit_dates is not None:
        return explicit_dates
    _validate_lookback_token(lookback)
    return None


def _raise_if_lookback_mixed_with_explicit_dates(
    *,
    start_date: str | None,
    end_date: str | None,
    lookback: str | None,
) -> None:
    """Reject lookback when explicit date bounds are also provided."""
    if lookback is None:
        return
    if start_date is not None:
        raise ValueError("lookback cannot be combined with start_date")
    if end_date is not None:
        raise ValueError("lookback cannot be combined with end_date")


def _resolve_explicit_dates(
    *,
    start_date: str | None,
    end_date: str | None,
    lookback: str | None,
) -> tuple[str, str] | None:
    """Return explicit dates when lookback is not requested."""
    if lookback is not None:
        return None
    if start_date is None and end_date is None:
        raise ValueError("either lookback or start_date and end_date must be provided")
    if start_date is None or end_date is None:
        raise ValueError("start_date and end_date must both be provided")
    return start_date, end_date


def _validate_lookback_token(lookback: str | None) -> None:
    """Validate the lookback token against supported values."""
    if lookback in _VALID_LOOKBACKS:
        return
    valid = ", ".join(_VALID_LOOKBACKS)
    raise ValueError(f"lookback must be one of: {valid}")


def _resolve_lookback_start_date(current: date, lookback: str) -> date:
    """Resolve the starting date for a validated lookback token."""
    month_lookback = {"1M": 1, "3M": 3, "6M": 6}
    if lookback == "1W":
        return current - timedelta(weeks=1)
    if lookback in month_lookback:
        return _subtract_months(current, month_lookback[lookback])
    if lookback == "1Y":
        try:
            return current.replace(year=current.year - 1)
        except ValueError:
            last_day = monthrange(current.year - 1, current.month)[1]
            return date(current.year - 1, current.month, last_day)
    return date(current.year, 1, 1)


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
        return types, and feature metadata. Can be called without
        instantiating a client (no authentication required).

        Returns:
            Dict with keys: auth_required, api_endpoint, methods.
        """
        return {
            "auth_required": True,
            "api_endpoint": GRAPHQL_URL,
            "methods": [
                {
                    "name": "get_stock",
                    "return_type": "StockData",
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
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                        {
                            "name": "start_date",
                            "type": "str | None",
                            "required": False,
                            "default": None,
                        },
                        {
                            "name": "end_date",
                            "type": "str | None",
                            "required": False,
                            "default": None,
                        },
                        {
                            "name": "lookback",
                            "type": "str | None",
                            "required": False,
                            "default": None,
                        },
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
                    "parameters": [
                        {"name": "list_id", "type": "int", "required": True},
                    ],
                },
                {
                    "name": "get_ownership",
                    "return_type": "OwnershipData",
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_watchlist_names",
                    "return_type": "list[WatchlistSummary]",
                    "parameters": [],
                },
                {
                    "name": "get_watchlist_symbols",
                    "return_type": "WatchlistDetail",
                    "parameters": [
                        {"name": "watchlist_id", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_screens",
                    "return_type": "list[Screen]",
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
                    "parameters": [
                        {"name": "symbol", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_active_alerts",
                    "return_type": "AlertSubscriptionList",
                    "parameters": [],
                },
                {
                    "name": "get_triggered_alerts",
                    "return_type": "TriggeredAlertList",
                    "parameters": [],
                },
                {
                    "name": "get_layouts",
                    "return_type": "list[Layout]",
                    "parameters": [],
                },
                {
                    "name": "get_chart_markups",
                    "return_type": "ChartMarkupList",
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
                    "parameters": [
                        {"name": "name", "type": "str", "required": True},
                    ],
                },
                {
                    "name": "get_screen_by_name",
                    "return_type": "Screen",
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
        symbol: str,
        symbol_dialect_type: str = "CHARTING",
    ) -> dict[str, Any]:
        today = date.today()
        pattern_end = today.isoformat()
        pattern_start = (today - timedelta(days=4 * 365)).isoformat()
        return {
            "operationName": "OtherMarketData",
            "variables": {
                "symbols": [symbol],
                "symbolDialectType": symbol_dialect_type,
                "upToHistoricalPeriodForProfitMargin": "P12Q_AGO",
                "upToHistoricalPeriodOffset": "P24Q_AGO",
                "upToQueryPeriodOffset": "P4Q_FUTURE",
            },
            "query": OTHER_MARKET_DATA_QUERY.replace(
                "{pattern_start_date}", pattern_start
            ).replace("{pattern_end_date}", pattern_end),
        }

    @staticmethod
    def _build_get_chart_data_payload(
        symbol: str,
        *,
        start_date: str,
        end_date: str,
        period: str = "P1D",
        exchange: str | None = None,
        benchmark: str | None = None,
    ) -> dict[str, Any]:
        """Build the GraphQL payload for chart data requests.

        When *exchange* is ``None``, the weekly query variant is used which
        omits the ``exchangeData`` section for a lighter response.  When an
        exchange name is provided, the full daily query is used instead.

        When *benchmark* is provided (e.g. ``"0S&P5"``), it is included as
        a second symbol so the response contains the benchmark time series
        needed to compute a relative strength line.
        """
        symbols = [symbol, benchmark] if benchmark else [symbol]
        variables: dict[str, Any] = {
            "symbols": symbols,
            "symbolDialectType": "CHARTING",
            "where": {
                "startDateTime": {"eq": start_date},
                "endDateTime": {"eq": end_date},
                "timeSeriesType": {"eq": period},
                "includeIntradayData": True,
            },
        }

        if exchange is None:
            query = CHART_MARKET_DATA_WEEKLY_QUERY
        else:
            variables["exchangeName"] = exchange
            query = CHART_MARKET_DATA_QUERY

        return {
            "operationName": "ChartMarketData",
            "variables": variables,
            "query": query,
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
    def _build_get_watchlist_symbols_payload(watchlist_id: str) -> dict[str, Any]:
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
    def _build_run_coach_screen_payload(screen_id: str) -> dict[str, Any]:
        """Build payload for the RunScreen query used by coach account screens.

        Coach screens (e.g. "William J. O'Neil", "Warren Buffett") use a
        different GraphQL operation than MarketDataScreen or
        MarketDataAdhocScreen.  They require `coachAccount: true` and
        the opaque screen ID from the CoachTree response.
        """
        return {
            "operationName": "RunScreen",
            "variables": {
                "input": {
                    "correlationTag": "marketsurge",
                    "coachAccount": True,
                    "pageSize": 1000,
                    "resultLimit": 1000000,
                    "screenId": screen_id,
                    "site": "marketsurge",
                    "skip": 0,
                    "responseColumns": WATCHLIST_COLUMNS,
                },
            },
            "query": RUN_SCREEN_QUERY,
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
    def _build_get_panels_payload() -> dict[str, Any]:
        return {
            "operationName": "AllPanels",
            "variables": {"site": "marketsurge"},
            "query": ALL_PANELS_QUERY,
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

    @staticmethod
    def _build_get_rs_rating_history_payload(symbol: str) -> dict[str, Any]:
        return {
            "operationName": "RSRatingRIPanel",
            "variables": {
                "symbols": [symbol],
                "symbolDialectType": "CHARTING",
            },
            "query": RS_RATING_RI_PANEL_QUERY,
        }

    @staticmethod
    def _build_get_server_time_payload() -> dict[str, Any]:
        return {
            "operationName": "GetServerDateTime",
            "variables": {},
            "query": GET_SERVER_DATE_TIME_QUERY,
        }

    @staticmethod
    def _build_get_nav_tree_payload() -> dict[str, Any]:
        return {
            "operationName": "NavTree",
            "variables": {"site": "marketsurge", "treeType": "MSR_NAV"},
            "query": NAV_TREE_QUERY,
        }

    @staticmethod
    def _build_get_coach_lists_payload() -> dict[str, Any]:
        return {
            "operationName": "CoachTree",
            "variables": {"site": "marketsurge", "treeType": "MSR_NAV"},
            "query": COACH_TREE_QUERY,
        }

    def _graphql_and_parse(
        self,
        payload: dict[str, Any],
        parse_fn: Callable[..., Any],
        *args: Any,
    ) -> Any:
        raw = self._graphql(payload)
        return parse_fn(raw, *args)

    def get_stock(
        self,
        symbol: str,
        symbol_dialect_type: str = "CHARTING",
    ) -> Any:
        payload = self._build_get_stock_payload(symbol, symbol_dialect_type)
        return self._graphql_and_parse(payload, parse_stock_response, symbol)

    def get_chart_data(
        self,
        symbol: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        lookback: str | None = None,
        period: str = "P1D",
        exchange: str | None = None,
        benchmark: str | None = None,
    ) -> Any:
        resolved_start_date, resolved_end_date = _resolve_chart_dates(
            start_date=start_date,
            end_date=end_date,
            lookback=lookback,
        )
        payload = self._build_get_chart_data_payload(
            symbol,
            start_date=resolved_start_date,
            end_date=resolved_end_date,
            period=period,
            exchange=exchange,
            benchmark=benchmark,
        )
        return self._graphql_and_parse(payload, parse_chart_data_response, symbol)

    def get_watchlist(self, list_id: int) -> Any:
        payload = self._build_get_watchlist_payload(list_id)
        return self._graphql_and_parse(payload, parse_watchlist_response)

    def get_ownership(self, symbol: str) -> Any:
        payload = self._build_get_ownership_payload(symbol)
        return self._graphql_and_parse(payload, parse_ownership_response, symbol)

    def get_watchlist_names(self) -> Any:
        payload = self._build_get_watchlist_names_payload()
        return self._graphql_and_parse(payload, parse_watchlists_response)

    def get_watchlist_symbols(self, watchlist_id: int) -> Any:
        payload = self._build_get_watchlist_symbols_payload(str(watchlist_id))
        return self._graphql_and_parse(
            payload, parse_watchlist_detail_response, str(watchlist_id)
        )

    def get_screens(
        self,
        screen_type: str | None = None,
        sort_dir: str | None = None,
    ) -> Any:
        payload = self._build_get_screens_payload(
            screen_type=screen_type, sort_dir=sort_dir
        )
        return self._graphql_and_parse(payload, parse_screens_response)

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

    @abstractmethod
    def get_stock_analysis(
        self, symbol: str
    ) -> StockAnalysis | Awaitable[StockAnalysis]:
        """Return stock plus optional fundamentals and ownership in one call."""

    def get_active_alerts(self) -> Any:
        payload = self._build_get_active_alerts_payload()
        return self._graphql_and_parse(payload, parse_active_alerts_response)

    def get_triggered_alerts(self) -> Any:
        payload = self._build_get_triggered_alerts_payload()
        return self._graphql_and_parse(payload, parse_triggered_alerts_response)

    def get_layouts(self) -> Any:
        payload = self._build_get_layouts_payload()
        return self._graphql_and_parse(payload, parse_layouts_response)

    def get_panels(self) -> Any:
        payload = self._build_get_panels_payload()
        return self._graphql_and_parse(payload, parse_panels_response)

    def get_chart_markups(
        self,
        symbol: str,
        *,
        frequency: str = "DAILY",
        sort_dir: str = "ASC",
    ) -> Any:
        payload = self._build_get_chart_markups_payload(
            symbol,
            frequency=frequency,
            sort_dir=sort_dir,
        )
        return self._graphql_and_parse(payload, parse_chart_markups_response)

    def get_rs_rating_history(self, symbol: str) -> Any:
        payload = self._build_get_rs_rating_history_payload(symbol)
        return self._graphql_and_parse(
            payload, parse_rs_rating_history_response, symbol
        )

    def get_server_time(self) -> Any:
        payload = self._build_get_server_time_payload()
        return self._graphql_and_parse(payload, parse_server_time_response)

    def get_nav_tree(self) -> Any:
        payload = self._build_get_nav_tree_payload()
        return self._graphql_and_parse(payload, parse_nav_tree_response)

    def get_coach_lists(self) -> Any:
        payload = self._build_get_coach_lists_payload()
        return self._graphql_and_parse(payload, parse_coach_tree_response)

    def run_report(self, report_id: int) -> Any:
        """Run a predefined MarketSurge report by its integer ID.

        Uses the same MarketDataAdhocScreen query as watchlists.
        Report IDs can be discovered via get_reports().

        Args:
            report_id: Integer ID of the report (e.g. 124 for Bases Forming).

        Returns:
            AdhocScreenResult with stock entries from the report.
        """
        payload = self._build_get_watchlist_payload(report_id)
        return self._graphql_and_parse(payload, parse_watchlist_response)

    def run_coach_screen(self, screen_id: str) -> Any:
        """Run a coach account screen by its opaque screen ID.

        Coach screens (e.g. "William J. O'Neil", "Warren Buffett") use
        the RunScreen GraphQL query with ``coachAccount: true``.  The
        screen ID comes from the CoachTree response
        (``NavTreeLeaf.reference_screen_id``).

        Args:
            screen_id: Opaque screen ID from the CoachTree.

        Returns:
            ScreenResult with row data from the coach screen.
        """
        payload = self._build_run_coach_screen_payload(screen_id)
        return self._graphql_and_parse(payload, parse_run_screen_response)


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
            status_code = exc.response.status_code
            response_body = exc.response.text
            if status_code == 429:
                message = "Rate limited, retry after a delay"
            elif status_code >= 500:
                message = "MarketSurge server error"
            else:
                message = f"HTTP error {status_code}"
            raise HTTPError(
                status_code=status_code,
                response_body=response_body,
                message=message,
            ) from exc
        return resp.json()

    def get_chart_data(
        self,
        symbol: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        lookback: str | None = None,
        period: str = "P1D",
        exchange: str | None = None,
        benchmark: str | None = None,
    ) -> ChartData:
        return super().get_chart_data(
            symbol,
            start_date=start_date,
            end_date=end_date,
            lookback=lookback,
            period=period,
            exchange=exchange,
            benchmark=benchmark,
        )

    def get_stock_analysis(self, symbol: str) -> StockAnalysis:
        """Return stock analysis with partial-failure handling for optional sections."""
        stock = self.get_stock(symbol)
        fundamentals = None
        ownership = None
        errors: list[str] = []

        try:
            fundamentals = self.get_fundamentals(symbol)
        except Exception as exc:
            errors.append(str(exc))

        try:
            ownership = self.get_ownership(symbol)
        except Exception as exc:
            errors.append(str(exc))

        return StockAnalysis(
            symbol=symbol,
            stock=stock,
            fundamentals=fundamentals,
            ownership=ownership,
            errors=errors,
        )

    def get_watchlist_by_name(self, name: str) -> WatchlistDetail:
        """Look up a watchlist by name and return its full details.

        Calls get_watchlist_names() to find the matching watchlist,
        then get_watchlist_symbols() to fetch all entries.

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
        return self.get_watchlist_symbols(match.id)

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

    def screen_watchlist_by_name(self, name: str) -> list[WatchlistEntry]:
        """Look up a watchlist by name and return its screened entries.

        Calls get_watchlist_names() to find the matching watchlist,
        then get_watchlist() to fetch all entries.

        Args:
            name: The exact name of the watchlist to look up.

        Returns:
            List of WatchlistEntry objects from the named watchlist.

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
        return self.get_watchlist(match.id)

    def get_reports(self) -> list[ReportInfo]:
        """Return all predefined MarketSurge reports.

        Returns the full hardcoded catalog of predefined reports
        (e.g. "Bases Forming", "Near Pivot", "Breaking Out Today").
        Any report can be run via ``run_report(original_id)`` regardless
        of whether the user has pinned it to their navigation sidebar.

        Returns:
            List of ReportInfo sorted by original_id.
        """
        return list(PREDEFINED_REPORTS)

    def run_report_by_name(self, name: str) -> AdhocScreenResult:
        """Run a predefined report by display name.

        Calls get_reports() to resolve the name to an integer ID,
        then runs the report via run_report().

        Args:
            name: Display name of the report (e.g. "Bases Forming").

        Returns:
            AdhocScreenResult with stock entries from the report.

        Raises:
            APIError: If no report matches the given name.
        """
        reports = self.get_reports()
        match = next((r for r in reports if r.name == name), None)
        if match is None:
            available = ", ".join(r.name for r in reports)
            raise APIError(
                f"No report found with name {name!r}. Available: {available or 'none'}"
            )
        return self.run_report(match.original_id)


class AsyncTickerScopeClient(BaseTickerScopeClient):
    """Authenticated async client for the MarketSurge GraphQL API."""

    def __init__(
        self,
        browser: str = "firefox",
        timeout: float = 30.0,
        *,
        jwt: str | None = None,
    ) -> None:
        self._jwt = resolve_jwt(jwt=jwt, browser=browser, timeout=timeout)
        self._http = httpx.AsyncClient(headers=self._build_headers(self._jwt))

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
    ) -> "AsyncTickerScopeClient":
        instance = object.__new__(cls)
        instance._jwt = await async_resolve_jwt(
            jwt=jwt, browser=browser, timeout=timeout
        )
        instance._http = httpx.AsyncClient(
            headers=instance._build_headers(instance._jwt)
        )
        return instance

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _graphql(self, payload: dict[str, Any]) -> dict[str, Any]:
        resp = await self._http.post(GRAPHQL_URL, json=payload)
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
            status_code = exc.response.status_code
            response_body = exc.response.text
            if status_code == 429:
                message = "Rate limited, retry after a delay"
            elif status_code >= 500:
                message = "MarketSurge server error"
            else:
                message = f"HTTP error {status_code}"
            raise HTTPError(
                status_code=status_code,
                response_body=response_body,
                message=message,
            ) from exc
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
    ) -> StockData:
        payload = self._build_get_stock_payload(symbol, symbol_dialect_type)
        return await self._graphql_and_parse(payload, parse_stock_response, symbol)

    async def get_chart_data(
        self,
        symbol: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        lookback: str | None = None,
        period: str = "P1D",
        exchange: str | None = None,
        benchmark: str | None = None,
    ) -> ChartData:
        resolved_start_date, resolved_end_date = _resolve_chart_dates(
            start_date=start_date,
            end_date=end_date,
            lookback=lookback,
        )
        payload = self._build_get_chart_data_payload(
            symbol,
            start_date=resolved_start_date,
            end_date=resolved_end_date,
            period=period,
            exchange=exchange,
            benchmark=benchmark,
        )
        return await self._graphql_and_parse(payload, parse_chart_data_response, symbol)

    async def get_stock_analysis(self, symbol: str) -> StockAnalysis:
        """Return stock analysis, tolerating optional endpoint failures."""
        stock_result, fundamentals_result, ownership_result = await asyncio.gather(
            self.get_stock(symbol),
            self.get_fundamentals(symbol),
            self.get_ownership(symbol),
            return_exceptions=True,
        )
        if isinstance(stock_result, Exception):
            raise stock_result

        fundamentals = (
            fundamentals_result
            if not isinstance(fundamentals_result, Exception)
            else None
        )
        ownership = (
            ownership_result if not isinstance(ownership_result, Exception) else None
        )
        errors: list[str] = []
        if isinstance(fundamentals_result, Exception):
            errors.append(str(fundamentals_result))
        if isinstance(ownership_result, Exception):
            errors.append(str(ownership_result))

        return StockAnalysis(
            symbol=symbol,
            stock=stock_result,
            fundamentals=fundamentals,
            ownership=ownership,
            errors=errors,
        )

    async def get_watchlist(self, list_id: int) -> list[WatchlistEntry]:
        payload = self._build_get_watchlist_payload(list_id)
        return await self._graphql_and_parse(payload, parse_watchlist_response)

    async def get_ownership(self, symbol: str) -> OwnershipData:
        payload = self._build_get_ownership_payload(symbol)
        return await self._graphql_and_parse(payload, parse_ownership_response, symbol)

    async def get_watchlist_names(self) -> list[WatchlistSummary]:
        payload = self._build_get_watchlist_names_payload()
        return await self._graphql_and_parse(payload, parse_watchlists_response)

    async def get_watchlist_symbols(self, watchlist_id: int) -> WatchlistDetail:
        payload = self._build_get_watchlist_symbols_payload(str(watchlist_id))
        return await self._graphql_and_parse(
            payload,
            parse_watchlist_detail_response,
            str(watchlist_id),
        )

    async def get_screens(
        self,
        screen_type: str | None = None,
        sort_dir: str | None = None,
    ) -> list[Screen]:
        payload = self._build_get_screens_payload(
            screen_type=screen_type, sort_dir=sort_dir
        )
        return await self._graphql_and_parse(payload, parse_screens_response)

    async def run_screen(
        self,
        screen_name: str,
        parameters: list[dict[str, str]],
    ) -> ScreenResult:
        payload = self._build_run_screen_payload(screen_name, parameters)
        return await self._graphql_and_parse(payload, parse_screen_result_response)

    async def get_fundamentals(self, symbol: str) -> FundamentalData:
        payload = self._build_get_fundamentals_payload(symbol)
        return await self._graphql_and_parse(
            payload, parse_fundamentals_response, symbol
        )

    async def get_active_alerts(self) -> AlertSubscriptionList:
        payload = self._build_get_active_alerts_payload()
        return await self._graphql_and_parse(payload, parse_active_alerts_response)

    async def get_triggered_alerts(self) -> TriggeredAlertList:
        payload = self._build_get_triggered_alerts_payload()
        return await self._graphql_and_parse(payload, parse_triggered_alerts_response)

    async def get_layouts(self) -> list[Layout]:
        payload = self._build_get_layouts_payload()
        return await self._graphql_and_parse(payload, parse_layouts_response)

    async def get_panels(self) -> list[Panel]:
        payload = self._build_get_panels_payload()
        return await self._graphql_and_parse(payload, parse_panels_response)

    async def get_chart_markups(
        self,
        symbol: str,
        *,
        frequency: str = "DAILY",
        sort_dir: str = "ASC",
    ) -> ChartMarkupList:
        payload = self._build_get_chart_markups_payload(
            symbol,
            frequency=frequency,
            sort_dir=sort_dir,
        )
        return await self._graphql_and_parse(payload, parse_chart_markups_response)

    async def get_rs_rating_history(self, symbol: str) -> RSRatingHistory:
        payload = self._build_get_rs_rating_history_payload(symbol)
        return await self._graphql_and_parse(
            payload, parse_rs_rating_history_response, symbol
        )

    async def get_server_time(self) -> datetime.datetime:
        payload = self._build_get_server_time_payload()
        return await self._graphql_and_parse(payload, parse_server_time_response)

    async def get_nav_tree(self) -> list[NavTreeNode]:
        payload = self._build_get_nav_tree_payload()
        return await self._graphql_and_parse(payload, parse_nav_tree_response)

    async def get_coach_lists(self) -> CoachTreeData:
        payload = self._build_get_coach_lists_payload()
        return await self._graphql_and_parse(payload, parse_coach_tree_response)

    async def get_watchlist_by_name(self, name: str) -> WatchlistDetail:
        """Look up a watchlist by name and return its full details.

        Calls get_watchlist_names() to find the matching watchlist,
        then get_watchlist_symbols() to fetch all entries.

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
        return await self.get_watchlist_symbols(match.id)

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

    async def screen_watchlist_by_name(self, name: str) -> list[WatchlistEntry]:
        """Look up a watchlist by name and return its screened entries.

        Calls get_watchlist_names() to find the matching watchlist,
        then get_watchlist() to fetch all entries.

        Args:
            name: The exact name of the watchlist to look up.

        Returns:
            List of WatchlistEntry objects from the named watchlist.

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
        return await self.get_watchlist(match.id)

    async def get_reports(self) -> list[ReportInfo]:
        """Return all predefined MarketSurge reports.

        Returns the full hardcoded catalog of predefined reports
        (e.g. "Bases Forming", "Near Pivot", "Breaking Out Today").
        Any report can be run via ``run_report(original_id)`` regardless
        of whether the user has pinned it to their navigation sidebar.

        Returns:
            List of ReportInfo sorted by original_id.
        """
        return list(PREDEFINED_REPORTS)

    async def run_report_by_name(self, name: str) -> AdhocScreenResult:
        """Run a predefined report by display name.

        Calls get_reports() to resolve the name to an integer ID,
        then runs the report via run_report().

        Args:
            name: Display name of the report (e.g. "Bases Forming").

        Returns:
            AdhocScreenResult with stock entries from the report.

        Raises:
            APIError: If no report matches the given name.
        """
        reports = await self.get_reports()
        match = next((r for r in reports if r.name == name), None)
        if match is None:
            available = ", ".join(r.name for r in reports)
            raise APIError(
                f"No report found with name {name!r}. Available: {available or 'none'}"
            )
        return await self.run_report(match.original_id)

    async def run_coach_screen(self, screen_id: str) -> ScreenResult:
        """Run a coach account screen by its opaque screen ID.

        Coach screens (e.g. "William J. O'Neil", "Warren Buffett") use
        the RunScreen GraphQL query with ``coachAccount: true``.  The
        screen ID comes from the CoachTree response
        (``NavTreeLeaf.reference_screen_id``).

        Args:
            screen_id: Opaque screen ID from the CoachTree.

        Returns:
            ScreenResult with row data from the coach screen.
        """
        payload = self._build_run_coach_screen_payload(screen_id)
        return await self._graphql_and_parse(payload, parse_run_screen_response)

    async def run_coach_screen_by_name(self, name: str) -> ScreenResult:
        """Run a coach account screen by display name.

        Queries the CoachTree to resolve the name to a screen ID, then
        runs the screen via run_coach_screen().

        Args:
            name: Display name of the coach screen
                (e.g. "William J. O'Neil", "Warren Buffett").

        Returns:
            ScreenResult with row data from the coach screen.

        Raises:
            APIError: If no coach screen matches the given name or the
                matching entry has no screen ID.
        """
        coach_data = await self.get_coach_lists()
        leaf = _find_coach_screen(coach_data.screens, name)
        if leaf is None:
            available = _list_coach_screen_names(coach_data.screens)
            raise APIError(
                f"No coach screen found with name {name!r}. "
                f"Available: {available or 'none'}"
            )
        if leaf.reference_screen_id is None:
            raise APIError(f"Coach screen {name!r} has no screen ID in its referenceId")
        return await self.run_coach_screen(leaf.reference_screen_id)
