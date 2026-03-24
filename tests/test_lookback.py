"""Tests for get_chart_data lookback date range support."""

from __future__ import annotations

# pyright: reportMissingImports=false

import inspect
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tickerscope._client import (
    AsyncTickerScopeClient,
    BaseTickerScopeClient,
    TickerScopeClient,
    _resolve_chart_dates,
)

FAKE_JWT = "fake.jwt.lookback"


@pytest.fixture
def sync_client() -> TickerScopeClient:
    """Create a sync client with mocked JWT resolution."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = TickerScopeClient(jwt=FAKE_JWT)
    yield client
    client.close()


@pytest.fixture
async def async_client() -> AsyncTickerScopeClient:
    """Create an async client with mocked JWT resolution."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient(jwt=FAKE_JWT)
    yield client
    await client.aclose()


def test_get_chart_data_signatures_include_lookback_and_optional_dates() -> None:
    """Expose lookback and optional start and end dates in all client classes."""
    for cls in (BaseTickerScopeClient, TickerScopeClient, AsyncTickerScopeClient):
        sig = inspect.signature(cls.get_chart_data)
        assert sig.parameters["start_date"].default is None
        assert sig.parameters["end_date"].default is None
        assert "lookback" in sig.parameters
        assert sig.parameters["lookback"].default is None


@pytest.mark.parametrize(
    ("lookback", "expected_start"),
    [
        ("1W", "2026-03-17"),
        ("1M", "2026-02-24"),
        ("3M", "2025-12-24"),
        ("6M", "2025-09-24"),
        ("1Y", "2025-03-24"),
        ("YTD", "2026-01-01"),
    ],
)
def test_resolve_chart_dates_for_all_lookbacks(
    lookback: str, expected_start: str
) -> None:
    """Resolve each supported lookback to the expected start and end dates."""
    start_date, end_date = _resolve_chart_dates(
        start_date=None,
        end_date=None,
        lookback=lookback,
        today=date(2026, 3, 24),
    )
    assert start_date == expected_start
    assert end_date == "2026-03-24"


def test_resolve_chart_dates_handles_end_of_month_rollover() -> None:
    """Resolve one month lookback from month-end to the last valid day."""
    start_date, end_date = _resolve_chart_dates(
        start_date=None,
        end_date=None,
        lookback="1M",
        today=date(2025, 3, 31),
    )
    assert start_date == "2025-02-28"
    assert end_date == "2025-03-31"


def test_resolve_chart_dates_handles_leap_year_month_rollover() -> None:
    """Resolve one month lookback from leap-year March 31 to February 29."""
    start_date, end_date = _resolve_chart_dates(
        start_date=None,
        end_date=None,
        lookback="1M",
        today=date(2024, 3, 31),
    )
    assert start_date == "2024-02-29"
    assert end_date == "2024-03-31"


def test_resolve_chart_dates_handles_january_year_rollover() -> None:
    """Resolve multi-month lookback across a year boundary."""
    start_date, end_date = _resolve_chart_dates(
        start_date=None,
        end_date=None,
        lookback="3M",
        today=date(2026, 1, 31),
    )
    assert start_date == "2025-10-31"
    assert end_date == "2026-01-31"


def test_resolve_chart_dates_rejects_mutual_exclusion_start_date() -> None:
    """Reject lookback when start_date is also provided."""
    with pytest.raises(ValueError, match="lookback cannot be combined with start_date"):
        _resolve_chart_dates(
            start_date="2026-01-01",
            end_date=None,
            lookback="1M",
            today=date(2026, 3, 24),
        )


def test_resolve_chart_dates_rejects_mutual_exclusion_end_date() -> None:
    """Reject lookback when end_date is also provided."""
    with pytest.raises(ValueError, match="lookback cannot be combined with end_date"):
        _resolve_chart_dates(
            start_date=None,
            end_date="2026-03-24",
            lookback="1M",
            today=date(2026, 3, 24),
        )


def test_resolve_chart_dates_rejects_missing_all_inputs() -> None:
    """Reject calls that provide neither lookback nor explicit dates."""
    with pytest.raises(ValueError, match="either lookback or start_date and end_date"):
        _resolve_chart_dates(
            start_date=None,
            end_date=None,
            lookback=None,
            today=date(2026, 3, 24),
        )


def test_resolve_chart_dates_rejects_incomplete_explicit_date_pair() -> None:
    """Reject calls that provide only one explicit date."""
    with pytest.raises(
        ValueError, match="start_date and end_date must both be provided"
    ):
        _resolve_chart_dates(
            start_date="2026-01-01",
            end_date=None,
            lookback=None,
            today=date(2026, 3, 24),
        )


def test_resolve_chart_dates_rejects_invalid_lookback_value() -> None:
    """Reject unsupported lookback values and list accepted values."""
    with pytest.raises(
        ValueError,
        match="lookback must be one of: 1W, 1M, 3M, 6M, 1Y, YTD",
    ):
        _resolve_chart_dates(
            start_date=None,
            end_date=None,
            lookback="2M",
            today=date(2026, 3, 24),
        )


def test_sync_get_chart_data_uses_resolved_dates_from_lookback(
    sync_client: TickerScopeClient,
) -> None:
    """Resolve lookback before calling the chart payload builder in sync client."""
    sync_client._build_get_chart_data_payload = MagicMock(return_value={})
    sentinel = object()
    sync_client._graphql_and_parse = MagicMock(return_value=sentinel)

    with patch("tickerscope._client._today", return_value=date(2026, 3, 24)):
        result = sync_client.get_chart_data("AAPL", lookback="YTD")

    assert result is sentinel
    sync_client._build_get_chart_data_payload.assert_called_once_with(
        "AAPL",
        start_date="2026-01-01",
        end_date="2026-03-24",
        period="P1D",
        exchange="NYSE",
    )


@pytest.mark.asyncio
async def test_async_get_chart_data_uses_resolved_dates_from_lookback(
    async_client: AsyncTickerScopeClient,
) -> None:
    """Resolve lookback before calling the chart payload builder in async client."""
    async_client._build_get_chart_data_payload = MagicMock(return_value={})
    sentinel = object()
    async_client._graphql_and_parse = AsyncMock(return_value=sentinel)

    with patch("tickerscope._client._today", return_value=date(2026, 3, 24)):
        result = await async_client.get_chart_data("AAPL", lookback="1W")

    assert result is sentinel
    async_client._build_get_chart_data_payload.assert_called_once_with(
        "AAPL",
        start_date="2026-03-17",
        end_date="2026-03-24",
        period="P1D",
        exchange="NYSE",
    )
