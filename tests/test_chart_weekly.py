"""Tests for weekly chart query variant that omits exchange data."""

from __future__ import annotations

# pyright: reportMissingImports=false

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import respx

from tickerscope._client import (
    AsyncTickerScopeClient,
    BaseTickerScopeClient,
    TickerScopeClient,
)
from tickerscope._parsing import parse_chart_data_response
from tickerscope._queries import (
    CHART_MARKET_DATA_QUERY,
    CHART_MARKET_DATA_WEEKLY_QUERY,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FAKE_JWT = "fake-jwt"
GRAPHQL_URL = "https://shared-data.dowjones.io/gateway/graphql"


def _load_chart_fixture() -> dict:
    """Load the chart data fixture from disk."""
    with open(FIXTURES_DIR / "chart_data_response.json") as f:
        return json.load(f)


def _chart_fixture_without_exchange() -> dict:
    """Return chart fixture with exchangeData removed."""
    raw = _load_chart_fixture()
    raw["data"].pop("exchangeData", None)
    return raw


class TestPayloadBuilderBranching:
    """Verify _build_get_chart_data_payload selects the right query variant."""

    def test_weekly_path_uses_weekly_query_when_exchange_is_none(self) -> None:
        """Use the weekly query and omit exchangeName when exchange is None."""
        payload = BaseTickerScopeClient._build_get_chart_data_payload(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
            exchange=None,
        )
        assert payload["query"] is CHART_MARKET_DATA_WEEKLY_QUERY
        assert "exchangeName" not in payload["variables"]

    def test_daily_path_uses_daily_query_when_exchange_is_provided(self) -> None:
        """Use the daily query and include exchangeName when exchange is set."""
        payload = BaseTickerScopeClient._build_get_chart_data_payload(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
            exchange="NYSE",
        )
        assert payload["query"] is CHART_MARKET_DATA_QUERY
        assert payload["variables"]["exchangeName"] == "NYSE"

    def test_default_exchange_is_none(self) -> None:
        """Default exchange parameter is None (weekly path)."""
        payload = BaseTickerScopeClient._build_get_chart_data_payload(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )
        assert payload["query"] is CHART_MARKET_DATA_WEEKLY_QUERY
        assert "exchangeName" not in payload["variables"]

    def test_shared_variables_present_on_both_paths(self) -> None:
        """Both weekly and daily payloads include the core variables."""
        for exchange in (None, "NYSE"):
            payload = BaseTickerScopeClient._build_get_chart_data_payload(
                "AAPL",
                start_date="2026-01-01",
                end_date="2026-03-01",
                exchange=exchange,
            )
            assert payload["operationName"] == "ChartMarketData"
            assert payload["variables"]["symbols"] == ["AAPL"]
            assert payload["variables"]["symbolDialectType"] == "CHARTING"
            assert payload["variables"]["where"]["timeSeriesType"] == {"eq": "P1D"}


class TestParserHandlesMissingExchangeData:
    """Verify parse_chart_data_response handles absent exchangeData."""

    def test_parser_returns_chart_data_without_exchange(self) -> None:
        """Parse a response with no exchangeData and get exchange=None."""
        raw = _chart_fixture_without_exchange()
        chart = parse_chart_data_response(raw, "TEST")
        assert chart is not None
        assert chart.exchange is None
        assert chart.symbol == "TEST"
        assert chart.time_series is not None

    def test_parser_returns_chart_data_with_exchange(self) -> None:
        """Parse the full response and get a populated exchange field."""
        raw = _load_chart_fixture()
        chart = parse_chart_data_response(raw, "TEST")
        assert chart is not None
        assert chart.exchange is not None
        assert chart.exchange.exchange_iso == "ARCX"


class TestSyncClientWeeklyPath:
    """Verify sync client uses weekly payload when exchange=None."""

    def test_sync_get_chart_data_weekly_calls_builder_with_none_exchange(
        self,
        sync_client: TickerScopeClient,
    ) -> None:
        """Pass exchange=None through to the payload builder."""
        sync_client._build_get_chart_data_payload = MagicMock(return_value={})
        sync_client._graphql_and_parse = MagicMock(return_value=None)

        sync_client.get_chart_data(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )

        sync_client._build_get_chart_data_payload.assert_called_once_with(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
            period="P1D",
            exchange=None,
            benchmark=None,
        )

    @respx.mock
    def test_sync_get_chart_data_weekly_roundtrip(
        self,
        sync_client: TickerScopeClient,
    ) -> None:
        """Full sync roundtrip with weekly response (no exchangeData)."""
        fixture = _chart_fixture_without_exchange()
        route = respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=fixture)
        )

        chart = sync_client.get_chart_data(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )

        assert route.call_count == 1
        assert chart.exchange is None
        assert chart.time_series is not None


class TestAsyncClientWeeklyPath:
    """Verify async client uses weekly payload when exchange=None."""

    @pytest.mark.asyncio
    async def test_async_get_chart_data_weekly_calls_builder_with_none_exchange(
        self,
        async_client: AsyncTickerScopeClient,
    ) -> None:
        """Pass exchange=None through to the payload builder in async client."""
        async_client._build_get_chart_data_payload = MagicMock(return_value={})
        async_client._graphql_and_parse = AsyncMock(return_value=None)

        await async_client.get_chart_data(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )

        async_client._build_get_chart_data_payload.assert_called_once_with(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
            period="P1D",
            exchange=None,
            benchmark=None,
        )

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_get_chart_data_weekly_roundtrip(
        self,
        async_client: AsyncTickerScopeClient,
    ) -> None:
        """Full async roundtrip with weekly response (no exchangeData)."""
        fixture = _chart_fixture_without_exchange()
        route = respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=fixture)
        )

        chart = await async_client.get_chart_data(
            "AAPL",
            start_date="2026-01-01",
            end_date="2026-03-01",
        )

        assert route.call_count == 1
        assert chart.exchange is None
        assert chart.time_series is not None
