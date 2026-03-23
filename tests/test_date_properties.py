"""Tests for date parsing functions and _dt properties on model dataclasses."""

from __future__ import annotations

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


class TestCompanyDtProperty:
    """Tests for Company.ipo_date_dt property."""

    def test_valid_ipo_date(self) -> None:
        """Valid ipo_date string parses to date object."""
        c = Company(
            name="Alphabet",
            industry=None,
            sector=None,
            industry_group_rank=None,
            industry_group_rs=None,
            industry_group_rs_letter=None,
            description=None,
            website=None,
            address=None,
            address2=None,
            phone=None,
            ipo_date="2004-08-19",
            ipo_price=85.0,
            ipo_price_formatted="85.00",
        )
        assert c.ipo_date_dt == datetime.date(2004, 8, 19)

    def test_none_ipo_date(self) -> None:
        """None ipo_date yields None from property."""
        c = Company(
            name="Test",
            industry=None,
            sector=None,
            industry_group_rank=None,
            industry_group_rs=None,
            industry_group_rs_letter=None,
            description=None,
            website=None,
            address=None,
            address2=None,
            phone=None,
            ipo_date=None,
            ipo_price=None,
            ipo_price_formatted=None,
        )
        assert c.ipo_date_dt is None

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain ipo_date_dt key."""
        c = Company(
            name="Test",
            industry=None,
            sector=None,
            industry_group_rank=None,
            industry_group_rs=None,
            industry_group_rs_letter=None,
            description=None,
            website=None,
            address=None,
            address2=None,
            phone=None,
            ipo_date="2004-08-19",
            ipo_price=None,
            ipo_price_formatted=None,
        )
        d = c.to_dict()
        assert "ipo_date_dt" not in d


class TestFinancialsDtProperties:
    """Tests for Financials._dt properties."""

    def test_eps_due_date_dt(self) -> None:
        """Valid eps_due_date string parses to date object."""
        f = Financials(
            eps_due_date="2026-04-28",
            eps_due_date_status="PROJECTED",
            eps_last_reported_date=None,
            eps_growth_rate=None,
            sales_growth_rate_3y=None,
            pre_tax_margin=None,
            after_tax_margin=None,
            gross_margin=None,
            return_on_equity=None,
            earnings_stability=None,
        )
        assert f.eps_due_date_dt == datetime.date(2026, 4, 28)

    def test_eps_last_reported_date_dt(self) -> None:
        """Valid eps_last_reported_date string parses to date object."""
        f = Financials(
            eps_due_date=None,
            eps_due_date_status=None,
            eps_last_reported_date="2026-02-04",
            eps_growth_rate=None,
            sales_growth_rate_3y=None,
            pre_tax_margin=None,
            after_tax_margin=None,
            gross_margin=None,
            return_on_equity=None,
            earnings_stability=None,
        )
        assert f.eps_last_reported_date_dt == datetime.date(2026, 2, 4)

    def test_none_dates(self) -> None:
        """None date fields yield None from properties."""
        f = Financials(
            eps_due_date=None,
            eps_due_date_status=None,
            eps_last_reported_date=None,
            eps_growth_rate=None,
            sales_growth_rate_3y=None,
            pre_tax_margin=None,
            after_tax_margin=None,
            gross_margin=None,
            return_on_equity=None,
            earnings_stability=None,
        )
        assert f.eps_due_date_dt is None
        assert f.eps_last_reported_date_dt is None

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain _dt keys."""
        f = Financials(
            eps_due_date="2026-04-28",
            eps_due_date_status=None,
            eps_last_reported_date="2026-02-04",
            eps_growth_rate=None,
            sales_growth_rate_3y=None,
            pre_tax_margin=None,
            after_tax_margin=None,
            gross_margin=None,
            return_on_equity=None,
            earnings_stability=None,
        )
        d = f.to_dict()
        assert "eps_due_date_dt" not in d
        assert "eps_last_reported_date_dt" not in d


class TestDividendDtProperty:
    """Tests for Dividend.ex_date_dt property."""

    def test_valid_ex_date(self) -> None:
        """Valid ex_date string parses to date object."""
        div = Dividend(ex_date="2024-06-10", amount="$0.20", change_indicator="UNKNOWN")
        assert div.ex_date_dt == datetime.date(2024, 6, 10)

    def test_none_ex_date(self) -> None:
        """None ex_date yields None from property."""
        div = Dividend(ex_date=None, amount=None, change_indicator=None)
        assert div.ex_date_dt is None


class TestCorporateActionsDtProperty:
    """Tests for CorporateActions.next_ex_dividend_date_dt property."""

    def test_valid_date(self) -> None:
        """Valid next_ex_dividend_date parses to date object."""
        ca = CorporateActions(
            next_ex_dividend_date="2026-03-09",
            dividends=[],
            splits=[],
            spinoffs=[],
        )
        assert ca.next_ex_dividend_date_dt == datetime.date(2026, 3, 9)

    def test_none_date(self) -> None:
        """None next_ex_dividend_date yields None from property."""
        ca = CorporateActions(
            next_ex_dividend_date=None,
            dividends=[],
            splits=[],
            spinoffs=[],
        )
        assert ca.next_ex_dividend_date_dt is None


class TestPatternDtProperties:
    """Tests for Pattern._dt properties (pivot, base_start, base_end)."""

    def test_all_dates_valid(self) -> None:
        """All three date properties parse valid strings."""
        p = Pattern(
            type="Cup With Handle",
            stage=1,
            base_number=1,
            status="COMPLETE",
            pivot_price=106.59,
            pivot_price_formatted="$106.59",
            pivot_date="2023-04-06",
            base_start_date="2023-02-08",
            base_end_date="2023-04-05",
            base_length=40,
        )
        assert p.pivot_date_dt == datetime.date(2023, 4, 6)
        assert p.base_start_date_dt == datetime.date(2023, 2, 8)
        assert p.base_end_date_dt == datetime.date(2023, 4, 5)

    def test_sentinel_pivot_date(self) -> None:
        """Sentinel '0001-01-01' pivot_date yields None (forming pattern)."""
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
        # base dates still parse fine
        assert p.base_start_date_dt == datetime.date(2026, 2, 3)

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain _dt keys."""
        p = Pattern(
            type="Flat Base",
            stage=2,
            base_number=2,
            status="COMPLETE",
            pivot_price=328.83,
            pivot_price_formatted="$328.83",
            pivot_date="2026-01-08",
            base_start_date="2025-11-26",
            base_end_date="2026-01-07",
            base_length=28,
        )
        d = p.to_dict()
        assert "pivot_date_dt" not in d
        assert "base_start_date_dt" not in d
        assert "base_end_date_dt" not in d


class TestFundamentalsDtProperty:
    """Tests for Fundamentals.new_ceo_date_dt property."""

    def test_valid_date(self) -> None:
        """Valid new_ceo_date parses to date object."""
        f = Fundamentals(
            r_and_d_percent_last_qtr=None,
            r_and_d_percent_last_qtr_formatted=None,
            debt_percent_formatted=None,
            new_ceo_date="2019-12-03",
        )
        assert f.new_ceo_date_dt == datetime.date(2019, 12, 3)

    def test_none_date(self) -> None:
        """None new_ceo_date yields None from property."""
        f = Fundamentals(
            r_and_d_percent_last_qtr=None,
            r_and_d_percent_last_qtr_formatted=None,
            debt_percent_formatted=None,
            new_ceo_date=None,
        )
        assert f.new_ceo_date_dt is None


class TestQuarterlyFundOwnershipDtProperty:
    """Tests for QuarterlyFundOwnership.date_dt property."""

    def test_valid_date(self) -> None:
        """Valid date string parses to date object."""
        q = QuarterlyFundOwnership(date="2025-12-31", count="245")
        assert q.date_dt == datetime.date(2025, 12, 31)

    def test_none_date(self) -> None:
        """None date yields None from property."""
        q = QuarterlyFundOwnership(date=None, count=None)
        assert q.date_dt is None


class TestReportedPeriodDtProperty:
    """Tests for ReportedPeriod.period_end_date_dt property."""

    def test_valid_date(self) -> None:
        """Valid period_end_date string parses to date object."""
        rp = ReportedPeriod(
            value=2.81,
            formatted_value="$2.81",
            pct_change_yoy=0.33,
            formatted_pct_change="+33%",
            period_offset="Y0",
            period_end_date="2025-12-31",
        )
        assert rp.period_end_date_dt == datetime.date(2025, 12, 31)

    def test_none_date(self) -> None:
        """None period_end_date yields None from property."""
        rp = ReportedPeriod(
            value=None,
            formatted_value=None,
            pct_change_yoy=None,
            formatted_pct_change=None,
            period_offset="Y0",
            period_end_date=None,
        )
        assert rp.period_end_date_dt is None


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


class TestDataPointDtProperties:
    """Tests for DataPoint._dt properties."""

    def test_start_and_end_dt(self) -> None:
        """Valid RFC 3339 strings parse into timezone-aware datetimes."""
        dp = DataPoint(
            start_date_time="2021-12-02T00:00:00.000-05:00",
            end_date_time="2021-12-02T23:59:59.000-05:00",
            open=100.0,
            high=105.0,
            low=99.0,
            close=103.0,
            volume=1000000.0,
        )
        assert dp.start_date_time_dt is not None
        assert dp.start_date_time_dt.tzinfo is not None
        assert dp.end_date_time_dt is not None
        assert dp.end_date_time_dt.tzinfo is not None

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain _dt keys."""
        dp = DataPoint(
            start_date_time="2021-12-02T00:00:00.000-05:00",
            end_date_time="2021-12-02T23:59:59.000-05:00",
            open=None,
            high=None,
            low=None,
            close=None,
            volume=None,
        )
        d = dp.to_dict()
        assert "start_date_time_dt" not in d
        assert "end_date_time_dt" not in d


class TestQuoteDtProperty:
    """Tests for Quote.trade_date_time_dt property."""

    def test_valid_datetime(self) -> None:
        """Valid trade_date_time parses into timezone-aware datetime."""
        q = Quote(
            trade_date_time="2026-03-20T16:00:00.000Z",
            timeliness=None,
            quote_type=None,
            last=150.0,
            volume=50000.0,
            percent_change=None,
            net_change=None,
        )
        result = q.trade_date_time_dt
        assert result is not None
        assert result.tzinfo is not None
        assert result.year == 2026

    def test_none_datetime(self) -> None:
        """None trade_date_time yields None from property."""
        q = Quote(
            trade_date_time=None,
            timeliness=None,
            quote_type=None,
            last=None,
            volume=None,
            percent_change=None,
            net_change=None,
        )
        assert q.trade_date_time_dt is None


class TestExchangeHolidayDtProperties:
    """Tests for ExchangeHoliday._dt properties."""

    def test_both_datetimes(self) -> None:
        """Both start and end datetimes parse as timezone-aware."""
        eh = ExchangeHoliday(
            name="Market Holiday",
            holiday_type="FULL",
            description=None,
            start_date_time="2026-01-01T00:00:00.000+00:00",
            end_date_time="2026-01-01T23:59:59.000+00:00",
        )
        assert eh.start_date_time_dt is not None
        assert eh.start_date_time_dt.tzinfo is not None
        assert eh.end_date_time_dt is not None


class TestWatchlistSummaryDtProperty:
    """Tests for WatchlistSummary.last_modified_dt property."""

    def test_valid_datetime(self) -> None:
        """Valid last_modified parses into timezone-aware datetime."""
        ws = WatchlistSummary(
            id="wl-123",
            name="My List",
            last_modified="2026-03-15T10:30:00.000Z",
            description=None,
        )
        result = ws.last_modified_dt
        assert result is not None
        assert result.tzinfo is not None

    def test_none_datetime(self) -> None:
        """None last_modified yields None from property."""
        ws = WatchlistSummary(id=None, name=None, last_modified=None, description=None)
        assert ws.last_modified_dt is None

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain last_modified_dt key."""
        ws = WatchlistSummary(
            id="wl-123",
            name="My List",
            last_modified="2026-03-15T10:30:00.000Z",
            description=None,
        )
        d = ws.to_dict()
        assert "last_modified_dt" not in d


class TestWatchlistDetailDtProperty:
    """Tests for WatchlistDetail.last_modified_dt property."""

    def test_valid_datetime(self) -> None:
        """Valid last_modified parses into timezone-aware datetime."""
        wd = WatchlistDetail(
            id="wl-456",
            name="Detail List",
            last_modified="2026-03-15T10:30:00.000Z",
            description=None,
            items=[],
        )
        result = wd.last_modified_dt
        assert result is not None
        assert result.tzinfo is not None

    def test_none_datetime(self) -> None:
        """None last_modified yields None from property."""
        wd = WatchlistDetail(
            id=None,
            name=None,
            last_modified=None,
            description=None,
            items=[],
        )
        assert wd.last_modified_dt is None


class TestScreenDtProperties:
    """Tests for Screen.created_at_dt and updated_at_dt properties."""

    def test_both_datetimes(self) -> None:
        """Both created_at and updated_at parse as timezone-aware datetimes."""
        s = Screen(
            id="scr-1",
            name="My Screen",
            type="USER",
            source=None,
            description=None,
            filter_criteria=None,
            created_at="2026-01-10T08:00:00.000Z",
            updated_at="2026-03-20T14:00:00.000Z",
        )
        assert s.created_at_dt is not None
        assert s.created_at_dt.tzinfo is not None
        assert s.updated_at_dt is not None
        assert s.updated_at_dt.year == 2026

    def test_none_datetimes(self) -> None:
        """None timestamp fields yield None from properties."""
        s = Screen(
            id=None,
            name=None,
            type=None,
            source=None,
            description=None,
            filter_criteria=None,
            created_at=None,
            updated_at=None,
        )
        assert s.created_at_dt is None
        assert s.updated_at_dt is None

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain _dt keys."""
        s = Screen(
            id="scr-1",
            name="Test",
            type="USER",
            source=None,
            description=None,
            filter_criteria=None,
            created_at="2026-01-10T08:00:00.000Z",
            updated_at="2026-03-20T14:00:00.000Z",
        )
        d = s.to_dict()
        assert "created_at_dt" not in d
        assert "updated_at_dt" not in d


class TestAlertSubscriptionDtProperty:
    """Tests for AlertSubscription.create_date_dt property."""

    def test_valid_datetime(self) -> None:
        """Valid create_date parses into timezone-aware datetime."""
        sub = AlertSubscription(
            delivery_preferences=[DeliveryPreference(method="EMAIL", type="IMMEDIATE")],
            criteria=None,
            create_date="2026-03-20T13:30:15.656Z",
            note=None,
        )
        result = sub.create_date_dt
        assert result is not None
        assert result.tzinfo is not None
        assert result.second == 15

    def test_none_datetime(self) -> None:
        """None create_date yields None from property."""
        sub = AlertSubscription(
            delivery_preferences=[],
            criteria=None,
            create_date=None,
            note=None,
        )
        assert sub.create_date_dt is None


class TestTriggeredAlertDtProperty:
    """Tests for TriggeredAlert.create_date_dt property."""

    def test_valid_datetime(self) -> None:
        """Valid create_date parses into timezone-aware datetime."""
        ta = TriggeredAlert(
            alert_id="alert-001",
            alert_type="PRICE",
            engine="STREAMING",
            delivery_preference=None,
            term=None,
            criteria_id=None,
            payload={},
            product=None,
            delivered=True,
            viewed=False,
            deleted=False,
            create_date="2026-03-20T13:30:15.656Z",
            ttl=None,
        )
        result = ta.create_date_dt
        assert result is not None
        assert result.tzinfo is not None
        assert result.microsecond == 656000

    def test_none_datetime(self) -> None:
        """None create_date yields None from property."""
        ta = TriggeredAlert(
            alert_id="alert-002",
            alert_type=None,
            engine=None,
            delivery_preference=None,
            term=None,
            criteria_id=None,
            payload={},
            product=None,
            delivered=False,
            viewed=False,
            deleted=False,
            create_date=None,
            ttl=None,
        )
        assert ta.create_date_dt is None


class TestChartMarkupDtProperties:
    """Tests for ChartMarkup.created_at_dt and updated_at_dt properties."""

    def test_both_datetimes(self) -> None:
        """Both created_at and updated_at parse as timezone-aware datetimes."""
        cm = ChartMarkup(
            id="cm-1",
            name="My Markup",
            data="{}",
            frequency="DAILY",
            site="MS",
            created_at="2026-01-10T08:00:00.000Z",
            updated_at="2026-03-20T14:00:00.000Z",
        )
        assert cm.created_at_dt is not None
        assert cm.created_at_dt.tzinfo is not None
        assert cm.updated_at_dt is not None

    def test_none_datetimes(self) -> None:
        """None timestamp fields yield None from properties."""
        cm = ChartMarkup(
            id="cm-2",
            name=None,
            data="{}",
            frequency=None,
            site=None,
            created_at=None,
            updated_at=None,
        )
        assert cm.created_at_dt is None
        assert cm.updated_at_dt is None

    def test_to_dict_excludes_dt(self) -> None:
        """to_dict() output does NOT contain _dt keys."""
        cm = ChartMarkup(
            id="cm-3",
            name="Test",
            data="{}",
            frequency=None,
            site=None,
            created_at="2026-01-10T08:00:00.000Z",
            updated_at="2026-03-20T14:00:00.000Z",
        )
        d = cm.to_dict()
        assert "created_at_dt" not in d
        assert "updated_at_dt" not in d


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
            "id": "wl-100",
            "name": "Test Watchlist",
            "last_modified": "2026-03-15T10:30:00.000Z",
            "description": None,
        }
        ws = WatchlistSummary.from_dict(data)
        assert ws.last_modified_dt is not None
        assert ws.last_modified_dt.tzinfo is not None
