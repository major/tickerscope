"""Tests for date parsing functions and _dt properties on model dataclasses."""

from __future__ import annotations

# pyright: reportMissingImports=false

import datetime

import pytest

from tickerscope._dates import parse_date, parse_date_list, parse_datetime
from tickerscope._models import (
    AlertSubscription,
    ChartMarkup,
    Company,
    CorporateActions,
    DataPoint,
    DeliveryPreference,
    Dividend,
    ExchangeHoliday,
    Financials,
    Fundamentals,
    Pattern,
    PricePercentChanges,
    Pricing,
    QuarterlyFundOwnership,
    Quote,
    ReportedPeriod,
    Screen,
    TriggeredAlert,
    WatchlistDetail,
    WatchlistSummary,
)


# ---------------------------------------------------------------------------
# parse_date()
# ---------------------------------------------------------------------------


class TestParseDateFunction:
    """Tests for the parse_date() utility function."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2004-08-19", datetime.date(2004, 8, 19)),
            ("2026-03-09", datetime.date(2026, 3, 9)),
            ("2023-12-31", datetime.date(2023, 12, 31)),
        ],
    )
    def test_valid_dates(self, raw: str, expected: datetime.date) -> None:
        """Valid ISO date strings parse into date objects."""
        assert parse_date(raw) == expected

    def test_none_returns_none(self) -> None:
        """None input yields None."""
        assert parse_date(None) is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string yields None."""
        assert parse_date("") is None

    def test_sentinel_returns_none(self) -> None:
        """MarketSurge sentinel '0001-01-01' yields None."""
        assert parse_date("0001-01-01") is None

    @pytest.mark.parametrize(
        "bad", ["not-a-date", "2024/01/15", "Jan 15 2024", "2024-13-01"]
    )
    def test_malformed_returns_none(self, bad: str) -> None:
        """Malformed strings yield None instead of raising."""
        assert parse_date(bad) is None


# ---------------------------------------------------------------------------
# parse_datetime()
# ---------------------------------------------------------------------------


class TestParseDatetimeFunction:
    """Tests for the parse_datetime() utility function."""

    def test_rfc3339_utc(self) -> None:
        """RFC 3339 timestamp with trailing Z is parsed as UTC."""
        result = parse_datetime("2026-03-20T13:30:15.656Z")
        assert result is not None
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 20
        assert result.hour == 13
        assert result.minute == 30
        assert result.second == 15
        assert result.tzinfo is not None

    def test_rfc3339_offset(self) -> None:
        """RFC 3339 timestamp with offset (-05:00) is parsed correctly."""
        result = parse_datetime("2021-12-02T00:00:00.000-05:00")
        assert result is not None
        assert result.year == 2021
        assert result.month == 12
        assert result.day == 2
        assert result.tzinfo is not None
        # Verify offset is preserved
        offset = result.utcoffset()
        assert offset == datetime.timedelta(hours=-5)

    def test_rfc3339_with_milliseconds(self) -> None:
        """Millisecond precision is preserved in parsed datetime."""
        result = parse_datetime("2026-03-20T13:30:15.656Z")
        assert result is not None
        assert result.microsecond == 656000

    def test_always_timezone_aware(self) -> None:
        """All successfully parsed datetimes have tzinfo set."""
        samples = [
            "2026-03-20T13:30:15.656Z",
            "2021-12-02T00:00:00.000-05:00",
            "2024-01-15T09:30:00+00:00",
        ]
        for raw in samples:
            result = parse_datetime(raw)
            assert result is not None, f"Failed to parse: {raw}"
            assert result.tzinfo is not None, f"Missing tzinfo for: {raw}"

    def test_naive_datetime_returns_none(self) -> None:
        """A valid datetime string WITHOUT timezone info returns None."""
        result = parse_datetime("2024-01-15T09:30:00")
        assert result is None

    def test_none_returns_none(self) -> None:
        """None input yields None."""
        assert parse_datetime(None) is None

    def test_empty_string_returns_none(self) -> None:
        """Empty string yields None."""
        assert parse_datetime("") is None

    @pytest.mark.parametrize(
        "bad", ["not-a-datetime", "2024-13-01T00:00:00Z", "garbage"]
    )
    def test_malformed_returns_none(self, bad: str) -> None:
        """Malformed strings yield None instead of raising."""
        assert parse_datetime(bad) is None


# ---------------------------------------------------------------------------
# parse_date_list()
# ---------------------------------------------------------------------------


class TestParseDateListFunction:
    """Tests for the parse_date_list() utility function."""

    def test_mixed_list(self) -> None:
        """List with valid dates, None, and sentinel values."""
        result = parse_date_list(["2026-01-08", None, "0001-01-01", "2024-06-10"])
        assert result == [
            datetime.date(2026, 1, 8),
            None,
            None,
            datetime.date(2024, 6, 10),
        ]

    def test_empty_list(self) -> None:
        """Empty input list produces empty output list."""
        assert parse_date_list([]) == []

    def test_all_valid(self) -> None:
        """All-valid list has no None elements in output."""
        result = parse_date_list(["2023-01-01", "2023-06-15"])
        assert all(isinstance(d, datetime.date) for d in result)
        assert len(result) == 2

    def test_preserves_length(self) -> None:
        """Output list length always matches input list length."""
        inputs: list[str | None] = [None, None, "bad", "2024-01-01"]
        result = parse_date_list(inputs)
        assert len(result) == len(inputs)


# ---------------------------------------------------------------------------
# _dt properties on models using parse_date()
# ---------------------------------------------------------------------------


def _assert_dt_property(
    model_class: type[object],
    constructor_kwargs: dict[str, object],
    field_name: str,
    input_value: str | None,
    expected: datetime.date | datetime.datetime | None,
) -> None:
    """Assert that a *_dt model property parses a date/datetime field correctly."""
    kwargs = dict(constructor_kwargs)
    kwargs[field_name] = input_value
    obj = model_class(**kwargs)  # pyright: ignore[reportCallIssue]
    result = getattr(obj, f"{field_name}_dt")
    assert result == expected


_COMPANY_NULLABLE_FIELDS = (
    "industry",
    "sector",
    "industry_group_rank",
    "industry_group_rs",
    "industry_group_rs_letter",
    "description",
    "website",
    "address",
    "address2",
    "phone",
)

_COMPANY_KWARGS: dict[str, object] = {
    "name": "Alphabet",
    "ipo_date": None,
    "ipo_price": 85.0,
    "ipo_price_formatted": "85.00",
    **dict.fromkeys(_COMPANY_NULLABLE_FIELDS, None),
}
_FINANCIALS_KWARGS: dict[str, object] = {
    "eps_due_date": None,
    "eps_due_date_status": "PROJECTED",
    "eps_last_reported_date": None,
    **dict.fromkeys(
        [
            "eps_growth_rate",
            "sales_growth_rate_3y",
            "pre_tax_margin",
            "after_tax_margin",
            "gross_margin",
            "return_on_equity",
            "earnings_stability",
        ],
        None,
    ),
}
_DIVIDEND_KWARGS: dict[str, object] = {
    "ex_date": None,
    "amount": "$0.20",
    "change_indicator": "UNKNOWN",
}
_CORPORATE_ACTIONS_KWARGS: dict[str, object] = {
    "next_ex_dividend_date": None,
    "dividends": [],
    "splits": [],
    "spinoffs": [],
}
_PATTERN_KWARGS: dict[str, object] = {
    "type": "Cup With Handle",
    "stage": 1,
    "base_number": 1,
    "status": "COMPLETE",
    "pivot_price": 106.59,
    "pivot_price_formatted": "$106.59",
    "pivot_date": None,
    "base_start_date": None,
    "base_end_date": None,
    "base_length": 40,
}
_FUNDAMENTALS_KWARGS: dict[str, object] = {
    **dict.fromkeys(
        [
            "r_and_d_percent_last_qtr",
            "r_and_d_percent_last_qtr_formatted",
            "debt_percent_formatted",
        ],
        None,
    ),
    "new_ceo_date": None,
}
_QUARTERLY_FUND_OWNERSHIP_KWARGS: dict[str, object] = {"date": None, "count": "245"}
_REPORTED_PERIOD_KWARGS: dict[str, object] = {
    "value": 2.81,
    "formatted_value": "$2.81",
    "pct_change_yoy": 0.33,
    "formatted_pct_change": "+33%",
    "period_offset": "Y0",
    "period_end_date": None,
}

_PARSE_DATE_DT_CASES = [
    (Company, _COMPANY_KWARGS, "ipo_date", "2004-08-19"),
    (Company, _COMPANY_KWARGS, "ipo_date", None),
    (Financials, _FINANCIALS_KWARGS, "eps_due_date", "2026-04-28"),
    (Financials, _FINANCIALS_KWARGS, "eps_due_date", None),
    (Financials, _FINANCIALS_KWARGS, "eps_last_reported_date", "2026-02-04"),
    (Financials, _FINANCIALS_KWARGS, "eps_last_reported_date", None),
    (Dividend, _DIVIDEND_KWARGS, "ex_date", "2024-06-10"),
    (Dividend, _DIVIDEND_KWARGS, "ex_date", None),
    (
        CorporateActions,
        _CORPORATE_ACTIONS_KWARGS,
        "next_ex_dividend_date",
        "2026-03-09",
    ),
    (CorporateActions, _CORPORATE_ACTIONS_KWARGS, "next_ex_dividend_date", None),
    (Pattern, _PATTERN_KWARGS, "pivot_date", "2023-04-06"),
    (Pattern, _PATTERN_KWARGS, "pivot_date", None),
    (Pattern, _PATTERN_KWARGS, "pivot_date", "0001-01-01"),
    (Pattern, _PATTERN_KWARGS, "base_start_date", "2023-02-08"),
    (Pattern, _PATTERN_KWARGS, "base_start_date", None),
    (Pattern, _PATTERN_KWARGS, "base_end_date", "2023-04-05"),
    (Pattern, _PATTERN_KWARGS, "base_end_date", None),
    (Fundamentals, _FUNDAMENTALS_KWARGS, "new_ceo_date", "2019-12-03"),
    (Fundamentals, _FUNDAMENTALS_KWARGS, "new_ceo_date", None),
    (QuarterlyFundOwnership, _QUARTERLY_FUND_OWNERSHIP_KWARGS, "date", "2025-12-31"),
    (QuarterlyFundOwnership, _QUARTERLY_FUND_OWNERSHIP_KWARGS, "date", None),
    (ReportedPeriod, _REPORTED_PERIOD_KWARGS, "period_end_date", "2025-12-31"),
    (ReportedPeriod, _REPORTED_PERIOD_KWARGS, "period_end_date", None),
]


@pytest.mark.parametrize(
    ("model_cls", "kwargs", "field_name", "input_value"),
    _PARSE_DATE_DT_CASES,
)
def test_parse_date_dt_properties(
    model_cls: type[object],
    kwargs: dict[str, object],
    field_name: str,
    input_value: str | None,
) -> None:
    """Date-backed *_dt model properties delegate to parse_date() correctly."""
    _assert_dt_property(
        model_cls, kwargs, field_name, input_value, parse_date(input_value)
    )


def test_pattern_pivot_date_sentinel_preserves_other_date_parsing() -> None:
    """Sentinel pivot_date maps to None while base_start_date still parses."""
    p = Pattern(
        type="Consolidation",
        stage=1,
        base_number=1,
        status="FORMING",
        pivot_price=349.0,
        pivot_price_formatted="$349.00",
        pivot_date="0001-01-01",
        base_start_date="2026-02-03",
        base_end_date="2026-03-19",
        base_length=32,
    )
    assert p.pivot_date_dt is None
    assert p.base_start_date_dt == datetime.date(2026, 2, 3)


# ---------------------------------------------------------------------------
# _dt properties on models using parse_date_list()
# ---------------------------------------------------------------------------


class TestPricingDtProperties:
    """Tests for Pricing.blue_dot_*_dates_dt properties."""

    def _make_pricing(
        self,
        daily: list[str | None] | None = None,
        weekly: list[str | None] | None = None,
    ) -> Pricing:
        """Build a Pricing instance with specified blue_dot lists."""
        return Pricing(
            market_cap=None,
            market_cap_formatted=None,
            avg_dollar_volume_50d=None,
            avg_dollar_volume_50d_formatted=None,
            up_down_volume_ratio=None,
            up_down_volume_ratio_formatted=None,
            atr_percent_21d=None,
            atr_percent_21d_formatted=None,
            short_interest_percent_float=None,
            short_interest_percent_float_formatted=None,
            blue_dot_daily_dates=daily or [],
            blue_dot_weekly_dates=weekly or [],
            price_percent_changes=PricePercentChanges(
                ytd=None,
                mtd=None,
                qtd=None,
                wtd=None,
                vs_1d=None,
                vs_1m=None,
                vs_3m=None,
                vs_year_high=None,
                vs_year_low=None,
            ),
            volume_percent_change_vs_50d=None,
        )

    def test_daily_dates_dt(self) -> None:
        """Valid blue_dot_daily_dates parse into date list."""
        p = self._make_pricing(daily=["2026-01-08"])
        result = p.blue_dot_daily_dates_dt
        assert result == [datetime.date(2026, 1, 8)]

    def test_weekly_dates_dt(self) -> None:
        """Valid blue_dot_weekly_dates parse into date list."""
        p = self._make_pricing(weekly=["2026-01-08", "2025-12-15"])
        result = p.blue_dot_weekly_dates_dt
        assert len(result) == 2
        assert result[0] == datetime.date(2026, 1, 8)

    def test_empty_lists(self) -> None:
        """Empty blue_dot lists produce empty output lists."""
        p = self._make_pricing()
        assert p.blue_dot_daily_dates_dt == []
        assert p.blue_dot_weekly_dates_dt == []

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain _dt keys."""
        p = self._make_pricing(daily=["2026-01-08"])
        d = p.to_dict()
        assert "blue_dot_daily_dates_dt" not in d
        assert "blue_dot_weekly_dates_dt" not in d


# ---------------------------------------------------------------------------
# _dt properties on models using parse_datetime()
# ---------------------------------------------------------------------------


_DATAPOINT_KWARGS: dict[str, object] = {
    "start_date_time": "2021-12-02T00:00:00.000-05:00",
    "end_date_time": "2021-12-02T23:59:59.000-05:00",
    **{"open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0},
    "volume": 1000000.0,
}
_QUOTE_KWARGS: dict[str, object] = {
    "trade_date_time": None,
    **dict.fromkeys(["timeliness", "quote_type"], None),
    "last": 150.0,
    "volume": 50000.0,
    **dict.fromkeys(["percent_change", "net_change"], None),
}
_EXCHANGE_HOLIDAY_KWARGS: dict[str, object] = {
    "name": "Market Holiday",
    "holiday_type": "FULL",
    "description": None,
    "start_date_time": "2026-01-01T00:00:00.000+00:00",
    "end_date_time": "2026-01-01T23:59:59.000+00:00",
}
_WATCHLIST_SUMMARY_KWARGS: dict[str, object] = {
    "id": 100,
    "name": "My List",
    "last_modified": None,
    "description": None,
}
_WATCHLIST_DETAIL_KWARGS: dict[str, object] = {
    "id": "wl-456",
    "name": "Detail List",
    "last_modified": None,
    "description": None,
    "items": [],
}
_SCREEN_KWARGS: dict[str, object] = {
    "id": "scr-1",
    "name": "My Screen",
    "type": "USER",
    **dict.fromkeys(["source", "description", "filter_criteria"], None),
    "created_at": None,
    "updated_at": None,
}
_ALERT_SUBSCRIPTION_KWARGS: dict[str, object] = {
    "delivery_preferences": [DeliveryPreference(method="EMAIL", type="IMMEDIATE")],
    "criteria": None,
    "create_date": None,
    "note": None,
}
_TRIGGERED_ALERT_KWARGS: dict[str, object] = {
    "alert_id": "alert-001",
    "alert_type": "PRICE",
    "engine": "STREAMING",
    **dict.fromkeys(["delivery_preference", "term", "criteria_id"], None),
    "payload": {},
    "product": None,
    "delivered": True,
    "viewed": False,
    "deleted": False,
    "create_date": None,
    "ttl": None,
}
_CHART_MARKUP_KWARGS: dict[str, object] = {
    "id": "cm-1",
    "name": "My Markup",
    "data": "{}",
    "frequency": "DAILY",
    "site": "MS",
    "created_at": None,
    "updated_at": None,
}

_PARSE_DATETIME_DT_CASES = [
    (DataPoint, _DATAPOINT_KWARGS, "start_date_time", "2021-12-02T00:00:00.000-05:00"),
    (DataPoint, _DATAPOINT_KWARGS, "end_date_time", "2021-12-02T23:59:59.000-05:00"),
    (Quote, _QUOTE_KWARGS, "trade_date_time", "2026-03-20T16:00:00.000Z"),
    (Quote, _QUOTE_KWARGS, "trade_date_time", None),
    (
        ExchangeHoliday,
        _EXCHANGE_HOLIDAY_KWARGS,
        "start_date_time",
        "2026-01-01T00:00:00.000+00:00",
    ),
    (
        ExchangeHoliday,
        _EXCHANGE_HOLIDAY_KWARGS,
        "end_date_time",
        "2026-01-01T23:59:59.000+00:00",
    ),
    (
        WatchlistSummary,
        _WATCHLIST_SUMMARY_KWARGS,
        "last_modified",
        "2026-03-15T10:30:00.000Z",
    ),
    (WatchlistSummary, _WATCHLIST_SUMMARY_KWARGS, "last_modified", None),
    (
        WatchlistDetail,
        _WATCHLIST_DETAIL_KWARGS,
        "last_modified",
        "2026-03-15T10:30:00.000Z",
    ),
    (WatchlistDetail, _WATCHLIST_DETAIL_KWARGS, "last_modified", None),
    (Screen, _SCREEN_KWARGS, "created_at", "2026-01-10T08:00:00.000Z"),
    (Screen, _SCREEN_KWARGS, "created_at", None),
    (Screen, _SCREEN_KWARGS, "updated_at", "2026-03-20T14:00:00.000Z"),
    (Screen, _SCREEN_KWARGS, "updated_at", None),
    (
        AlertSubscription,
        _ALERT_SUBSCRIPTION_KWARGS,
        "create_date",
        "2026-03-20T13:30:15.656Z",
    ),
    (AlertSubscription, _ALERT_SUBSCRIPTION_KWARGS, "create_date", None),
    (
        TriggeredAlert,
        _TRIGGERED_ALERT_KWARGS,
        "create_date",
        "2026-03-20T13:30:15.656Z",
    ),
    (TriggeredAlert, _TRIGGERED_ALERT_KWARGS, "create_date", None),
    (ChartMarkup, _CHART_MARKUP_KWARGS, "created_at", "2026-01-10T08:00:00.000Z"),
    (ChartMarkup, _CHART_MARKUP_KWARGS, "created_at", None),
    (ChartMarkup, _CHART_MARKUP_KWARGS, "updated_at", "2026-03-20T14:00:00.000Z"),
    (ChartMarkup, _CHART_MARKUP_KWARGS, "updated_at", None),
]


@pytest.mark.parametrize(
    ("model_cls", "kwargs", "field_name", "input_value"),
    _PARSE_DATETIME_DT_CASES,
)
def test_parse_datetime_dt_properties(
    model_cls: type[object],
    kwargs: dict[str, object],
    field_name: str,
    input_value: str | None,
) -> None:
    """Datetime-backed *_dt model properties delegate to parse_datetime() correctly."""
    _assert_dt_property(
        model_cls,
        kwargs,
        field_name,
        input_value,
        parse_datetime(input_value),
    )


class TestToDictExcludesDt:
    """Representative checks that computed *_dt properties are not serialized."""

    def test_company_to_dict_excludes_ipo_date_dt(self) -> None:
        """Company.to_dict() excludes computed ipo_date_dt field."""
        company = Company(**{**_COMPANY_KWARGS, "ipo_date": "2004-08-19"})
        assert "ipo_date_dt" not in company.to_dict()

    def test_screen_to_dict_excludes_created_and_updated_dt(self) -> None:
        """Screen.to_dict() excludes created_at_dt and updated_at_dt fields."""
        screen = Screen(
            **{
                **_SCREEN_KWARGS,
                "created_at": "2026-01-10T08:00:00.000Z",
                "updated_at": "2026-03-20T14:00:00.000Z",
            }
        )
        data = screen.to_dict()
        assert "created_at_dt" not in data
        assert "updated_at_dt" not in data


# ---------------------------------------------------------------------------
# from_dict() round-trip still works after properties were added
# ---------------------------------------------------------------------------


class TestFromDictRoundTrip:
    """Verify from_dict() still works on models with _dt properties."""

    def test_company_from_dict(self) -> None:
        """Company.from_dict() round-trip succeeds with date fields."""
        data = {
            "name": "Alphabet",
            "industry": "Internet-Content",
            "sector": "INTERNET",
            "industry_group_rank": 160,
            "industry_group_rs": None,
            "industry_group_rs_letter": None,
            "description": None,
            "website": None,
            "address": None,
            "address2": None,
            "phone": None,
            "ipo_date": "2004-08-19",
            "ipo_price": 85.0,
            "ipo_price_formatted": "85.00",
        }
        c = Company.from_dict(data)
        assert c.ipo_date == "2004-08-19"
        assert c.ipo_date_dt == datetime.date(2004, 8, 19)

    def test_pattern_from_dict(self) -> None:
        """Pattern.from_dict() round-trip succeeds with sentinel date."""
        data = {
            "type": "Consolidation",
            "stage": 1,
            "base_number": 1,
            "status": "FORMING",
            "pivot_price": 349.0,
            "pivot_price_formatted": "$349.00",
            "pivot_date": "0001-01-01",
            "base_start_date": "2026-02-03",
            "base_end_date": "2026-03-19",
            "base_length": 32,
        }
        p = Pattern.from_dict(data)
        assert p.pivot_date_dt is None
        assert p.base_start_date_dt == datetime.date(2026, 2, 3)

    def test_watchlist_summary_from_dict(self) -> None:
        """WatchlistSummary.from_dict() round-trip succeeds with datetime field."""
        data = {
            "id": 100,
            "name": "Test Watchlist",
            "last_modified": "2026-03-15T10:30:00.000Z",
            "description": None,
        }
        ws = WatchlistSummary.from_dict(data)
        assert ws.last_modified_dt is not None
        assert ws.last_modified_dt.tzinfo is not None
