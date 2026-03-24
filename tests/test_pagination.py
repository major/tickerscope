"""Tests for limit and max_points pagination parameters on client methods."""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
import respx

from tickerscope._client import AsyncTickerScopeClient, TickerScopeClient

GRAPHQL_URL = "https://shared-data.dowjones.io/gateway/graphql"
FAKE_JWT = "fake_jwt_pagination"


@pytest.fixture
def sync_client():
    """Create a sync TickerScopeClient with mocked authentication."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        c = TickerScopeClient()
    yield c
    c.close()


@pytest.fixture
async def async_client():
    """Create an async TickerScopeClient with mocked authentication."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        c = AsyncTickerScopeClient()
    yield c
    await c.aclose()


# ── get_watchlists: plain list, fixture has 2 items ─────────────────────


class TestWatchlistNamesLimitSync:
    """Sync limit tests for get_watchlists (returns plain list)."""

    @respx.mock
    def test_default_returns_all(self, sync_client, watchlist_names_response):
        """No limit returns the full list."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        result = sync_client.get_watchlists()
        assert len(result) == 2

    @respx.mock
    def test_limit_two_returns_two(self, sync_client, watchlist_names_response):
        """limit=2 returns first 2 items (all available in this fixture)."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        result = sync_client.get_watchlists(limit=2)
        assert len(result) == 2

    @respx.mock
    def test_limit_one_truncates(self, sync_client, watchlist_names_response):
        """limit=1 truncates to a single item, preserving order."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        result = sync_client.get_watchlists(limit=1)
        assert len(result) == 1
        assert result[0].name == "My Watchlist"

    @respx.mock
    def test_limit_zero_returns_empty(self, sync_client, watchlist_names_response):
        """limit=0 returns an empty list."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        assert sync_client.get_watchlists(limit=0) == []

    @respx.mock
    def test_limit_exceeding_count_returns_all(
        self, sync_client, watchlist_names_response
    ):
        """limit > available items returns all items without error."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        assert len(sync_client.get_watchlists(limit=100)) == 2

    @respx.mock
    def test_negative_limit_raises(self, sync_client, watchlist_names_response):
        """Negative limit raises ValueError."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        with pytest.raises(ValueError, match="limit must be non-negative"):
            sync_client.get_watchlists(limit=-1)


class TestWatchlistNamesLimitAsync:
    """Async limit tests for get_watchlists (returns plain list)."""

    @respx.mock
    async def test_default_returns_all(self, async_client, watchlist_names_response):
        """No limit returns the full list."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        result = await async_client.get_watchlists()
        assert len(result) == 2

    @respx.mock
    async def test_limit_two_returns_two(self, async_client, watchlist_names_response):
        """limit=2 returns first 2 items."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        result = await async_client.get_watchlists(limit=2)
        assert len(result) == 2

    @respx.mock
    async def test_limit_one_truncates(self, async_client, watchlist_names_response):
        """limit=1 truncates to a single item, preserving order."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        result = await async_client.get_watchlists(limit=1)
        assert len(result) == 1
        assert result[0].name == "My Watchlist"

    @respx.mock
    async def test_limit_zero_returns_empty(
        self, async_client, watchlist_names_response
    ):
        """limit=0 returns an empty list."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        assert await async_client.get_watchlists(limit=0) == []

    @respx.mock
    async def test_limit_exceeding_count_returns_all(
        self, async_client, watchlist_names_response
    ):
        """limit > available items returns all items without error."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        assert len(await async_client.get_watchlists(limit=100)) == 2

    @respx.mock
    async def test_negative_limit_raises(self, async_client, watchlist_names_response):
        """Negative limit raises ValueError."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=watchlist_names_response)
        )
        with pytest.raises(ValueError, match="limit must be non-negative"):
            await async_client.get_watchlists(limit=-1)


# ── get_active_alerts: wrapper object, fixture has 3 subscriptions ───────────


class TestActiveAlertsLimitSync:
    """Sync limit tests for get_active_alerts (AlertSubscriptionList wrapper)."""

    @respx.mock
    def test_default_returns_all_with_metadata(
        self, sync_client, active_alerts_response
    ):
        """No limit returns all subscriptions and metadata intact."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = sync_client.get_active_alerts()
        assert len(result.subscriptions) == 3
        assert result.num_subscriptions == 3
        assert result.remaining_subscriptions == 747

    @respx.mock
    def test_limit_truncates_list_preserves_metadata(
        self, sync_client, active_alerts_response
    ):
        """limit=2 truncates subscriptions but preserves count fields."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = sync_client.get_active_alerts(limit=2)
        assert len(result.subscriptions) == 2
        assert result.num_subscriptions == 3
        assert result.remaining_subscriptions == 747

    @respx.mock
    def test_limit_zero_empties_list_preserves_metadata(
        self, sync_client, active_alerts_response
    ):
        """limit=0 returns empty subscriptions but metadata still intact."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = sync_client.get_active_alerts(limit=0)
        assert len(result.subscriptions) == 0
        assert result.num_subscriptions == 3
        assert result.remaining_subscriptions == 747

    @respx.mock
    def test_limit_exceeding_count_returns_all(
        self, sync_client, active_alerts_response
    ):
        """limit > subscriptions count returns all subscriptions."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = sync_client.get_active_alerts(limit=100)
        assert len(result.subscriptions) == 3

    @respx.mock
    def test_negative_limit_raises(self, sync_client, active_alerts_response):
        """Negative limit raises ValueError."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        with pytest.raises(ValueError, match="limit must be non-negative"):
            sync_client.get_active_alerts(limit=-1)


class TestActiveAlertsLimitAsync:
    """Async limit tests for get_active_alerts (AlertSubscriptionList wrapper)."""

    @respx.mock
    async def test_default_returns_all_with_metadata(
        self, async_client, active_alerts_response
    ):
        """No limit returns all subscriptions and metadata intact."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = await async_client.get_active_alerts()
        assert len(result.subscriptions) == 3
        assert result.num_subscriptions == 3
        assert result.remaining_subscriptions == 747

    @respx.mock
    async def test_limit_truncates_list_preserves_metadata(
        self, async_client, active_alerts_response
    ):
        """limit=2 truncates subscriptions but preserves count fields."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = await async_client.get_active_alerts(limit=2)
        assert len(result.subscriptions) == 2
        assert result.num_subscriptions == 3
        assert result.remaining_subscriptions == 747

    @respx.mock
    async def test_limit_zero_empties_list_preserves_metadata(
        self, async_client, active_alerts_response
    ):
        """limit=0 returns empty subscriptions but metadata still intact."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = await async_client.get_active_alerts(limit=0)
        assert len(result.subscriptions) == 0
        assert result.num_subscriptions == 3
        assert result.remaining_subscriptions == 747

    @respx.mock
    async def test_limit_exceeding_count_returns_all(
        self, async_client, active_alerts_response
    ):
        """limit > subscriptions count returns all subscriptions."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        result = await async_client.get_active_alerts(limit=100)
        assert len(result.subscriptions) == 3

    @respx.mock
    async def test_negative_limit_raises(self, async_client, active_alerts_response):
        """Negative limit raises ValueError."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=active_alerts_response)
        )
        with pytest.raises(ValueError, match="limit must be non-negative"):
            await async_client.get_active_alerts(limit=-1)


# ── get_chart_data: max_points on time_series.data_points (3 in fixture) ─────


class TestChartDataMaxPointsSync:
    """Sync tests for get_chart_data max_points parameter."""

    @respx.mock
    def test_default_returns_all_data_points(self, sync_client, chart_data_response):
        """No max_points returns all data points."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = sync_client.get_chart_data(
            "TEST", start_date="2021-12-01", end_date="2021-12-31"
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 3

    @respx.mock
    def test_max_points_truncates(self, sync_client, chart_data_response):
        """max_points=2 truncates data_points to first 2."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = sync_client.get_chart_data(
            "TEST",
            start_date="2021-12-01",
            end_date="2021-12-31",
            max_points=2,
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 2

    @respx.mock
    def test_max_points_zero_returns_empty(self, sync_client, chart_data_response):
        """max_points=0 returns empty data_points list."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = sync_client.get_chart_data(
            "TEST",
            start_date="2021-12-01",
            end_date="2021-12-31",
            max_points=0,
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 0

    @respx.mock
    def test_max_points_exceeding_returns_all(self, sync_client, chart_data_response):
        """max_points > available points returns all data points."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = sync_client.get_chart_data(
            "TEST",
            start_date="2021-12-01",
            end_date="2021-12-31",
            max_points=100,
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 3

    @respx.mock
    def test_negative_max_points_raises(self, sync_client, chart_data_response):
        """Negative max_points raises ValueError."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        with pytest.raises(ValueError, match="max_points must be non-negative"):
            sync_client.get_chart_data(
                "TEST",
                start_date="2021-12-01",
                end_date="2021-12-31",
                max_points=-1,
            )


class TestChartDataMaxPointsAsync:
    """Async tests for get_chart_data max_points parameter."""

    @respx.mock
    async def test_default_returns_all_data_points(
        self, async_client, chart_data_response
    ):
        """No max_points returns all data points."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = await async_client.get_chart_data(
            "TEST", start_date="2021-12-01", end_date="2021-12-31"
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 3

    @respx.mock
    async def test_max_points_truncates(self, async_client, chart_data_response):
        """max_points=2 truncates data_points to first 2."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = await async_client.get_chart_data(
            "TEST",
            start_date="2021-12-01",
            end_date="2021-12-31",
            max_points=2,
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 2

    @respx.mock
    async def test_max_points_zero_returns_empty(
        self, async_client, chart_data_response
    ):
        """max_points=0 returns empty data_points list."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = await async_client.get_chart_data(
            "TEST",
            start_date="2021-12-01",
            end_date="2021-12-31",
            max_points=0,
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 0

    @respx.mock
    async def test_max_points_exceeding_returns_all(
        self, async_client, chart_data_response
    ):
        """max_points > available points returns all data points."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        result = await async_client.get_chart_data(
            "TEST",
            start_date="2021-12-01",
            end_date="2021-12-31",
            max_points=100,
        )
        assert result.time_series is not None
        assert len(result.time_series.data_points) == 3

    @respx.mock
    async def test_negative_max_points_raises(self, async_client, chart_data_response):
        """Negative max_points raises ValueError."""
        respx.post(GRAPHQL_URL).mock(
            return_value=httpx.Response(200, json=chart_data_response)
        )
        with pytest.raises(ValueError, match="max_points must be non-negative"):
            await async_client.get_chart_data(
                "TEST",
                start_date="2021-12-01",
                end_date="2021-12-31",
                max_points=-1,
            )
