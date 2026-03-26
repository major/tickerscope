"""Tests for frozen dataclass models."""

from __future__ import annotations

# pyright: reportMissingImports=false

import pytest

from tickerscope._models import (
    BasicOwnership,
    Company,
    CorporateActions,
    Financials,
    Fundamentals,
    HistoricalPriceStatistic,
    Industry,
    IndustryGroupSnapshot,
    PricePercentChanges,
    Pricing,
    Quote,
    Ratings,
    StockData,
    VolumeMovingAverage,
)


class TestRatings:
    """Tests for the Ratings dataclass."""

    def test_frozen_enforcement(self) -> None:
        """Frozen dataclass rejects attribute assignment."""
        r = Ratings(composite=95, eps=88, rs=92, smr="A", ad="B")
        with pytest.raises(AttributeError):
            r.composite = 50  # type: ignore[misc]


class TestStockData:
    """Tests for the fully nested StockData dataclass."""

    def test_frozen_enforcement(self) -> None:
        """StockData rejects attribute assignment."""
        stock = StockData(
            symbol="AAPL",
            ratings=Ratings(composite=95, eps=88, rs=92, smr="A", ad="B"),
            company=Company(
                name="Apple Inc",
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
            ),
            pricing=Pricing(
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
                blue_dot_daily_dates=[],
                blue_dot_weekly_dates=[],
                ant_dates=[],
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
            ),
            financials=Financials(
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
            ),
            corporate_actions=CorporateActions(
                next_ex_dividend_date=None,
                dividends=[],
                splits=[],
                spinoffs=[],
            ),
            industry=Industry(name=None, sector=None, code=None, number_of_stocks=None),
            ownership=BasicOwnership(
                funds_float_pct=None, funds_float_pct_formatted=None
            ),
            fundamentals=Fundamentals(
                r_and_d_percent_last_qtr=None,
                r_and_d_percent_last_qtr_formatted=None,
                debt_percent_formatted=None,
                new_ceo_date=None,
            ),
            quarterly_financials=None,
            patterns=[],
            tight_areas=[],
        )
        with pytest.raises(AttributeError):
            stock.symbol = "GOOG"  # type: ignore[misc]


class TestAllImportable:
    """Verify all 15 dataclass names are importable from tickerscope._models."""

    def test_all_classes_importable(self) -> None:
        """All 15 dataclass names resolve from the _models module."""
        from tickerscope import _models

        expected_classes = [
            "Ratings",
            "Company",
            "PricePercentChanges",
            "Pricing",
            "Financials",
            "Dividend",
            "CorporateActions",
            "Pattern",
            "Industry",
            "BasicOwnership",
            "Fundamentals",
            "StockData",
            "WatchlistEntry",
            "QuarterlyFundOwnership",
            "OwnershipData",
        ]
        for name in expected_classes:
            cls = getattr(_models, name)
            assert callable(cls), f"{name} is not callable"


class TestQuoteCloseAlias:
    """Tests for Quote.close property alias."""

    def test_close_returns_last_value(self) -> None:
        """Quote.close returns the same value as Quote.last."""
        q = Quote(
            trade_date_time=None,
            timeliness=None,
            quote_type=None,
            last=42.5,
            volume=None,
            percent_change=None,
            net_change=None,
        )
        assert q.close == 42.5
        assert q.close == q.last

    def test_close_is_none_when_last_is_none(self) -> None:
        """Quote.close returns None when last is None."""
        q = Quote(
            trade_date_time=None,
            timeliness=None,
            quote_type=None,
            last=None,
            volume=None,
            percent_change=None,
            net_change=None,
        )
        assert q.close is None

    def test_close_not_in_to_dict_output(self) -> None:
        """Quote.close is a property so it does not appear in to_dict() output."""
        q = Quote(
            trade_date_time=None,
            timeliness=None,
            quote_type=None,
            last=42.5,
            volume=None,
            percent_change=None,
            net_change=None,
        )
        d = q.to_dict()
        assert "close" not in d
        assert "last" in d


class TestIndustryGroupSnapshot:
    """Tests for the IndustryGroupSnapshot dataclass."""

    def test_frozen_enforcement(self) -> None:
        """Frozen dataclass rejects attribute assignment."""
        snapshot = IndustryGroupSnapshot(period_offset="CURRENT", value=160)
        with pytest.raises(AttributeError):
            snapshot.value = 100  # type: ignore[misc]

    def test_from_dict_round_trip(self) -> None:
        """from_dict reconstructs instance from to_dict output."""
        original = IndustryGroupSnapshot(
            period_offset="CURRENT", value=160, letter_value="A"
        )
        data = original.to_dict()
        reconstructed = IndustryGroupSnapshot.from_dict(data)
        assert reconstructed.period_offset == "CURRENT"
        assert reconstructed.value == 160
        assert reconstructed.letter_value == "A"

    def test_period_offset_required(self) -> None:
        """period_offset is required (no default)."""
        snapshot = IndustryGroupSnapshot(period_offset="P1Q_AGO")
        assert snapshot.period_offset == "P1Q_AGO"
        assert snapshot.value is None
        assert snapshot.letter_value is None


class TestHistoricalPriceStatistic:
    """Tests for the HistoricalPriceStatistic dataclass."""

    def test_frozen_enforcement(self) -> None:
        """Frozen dataclass rejects attribute assignment."""
        stat = HistoricalPriceStatistic(
            period="P1Q", period_offset="P1Q_AGO", price_close=313.0
        )
        with pytest.raises(AttributeError):
            stat.price_close = 100.0  # type: ignore[misc]

    def test_from_dict_round_trip(self) -> None:
        """from_dict reconstructs instance from to_dict output."""
        original = HistoricalPriceStatistic(
            period="P1Q",
            period_offset="P1Q_AGO",
            period_end_date="2025-12-31",
            price_high_date="2025-12-20",
            price_high=320.0,
            price_low_date="2025-12-01",
            price_low=310.0,
            price_close=313.0,
            price_percent_change=1.5,
        )
        data = original.to_dict()
        reconstructed = HistoricalPriceStatistic.from_dict(data)
        assert reconstructed.period == "P1Q"
        assert reconstructed.period_offset == "P1Q_AGO"
        assert reconstructed.period_end_date == "2025-12-31"
        assert reconstructed.price_close == 313.0

    def test_period_end_date_dt_property(self) -> None:
        """period_end_date_dt parses date string correctly."""
        stat = HistoricalPriceStatistic(period_end_date="2025-12-31")
        dt = stat.period_end_date_dt
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 31

    def test_price_high_date_dt_property(self) -> None:
        """price_high_date_dt parses date string correctly."""
        stat = HistoricalPriceStatistic(price_high_date="2025-12-20")
        dt = stat.price_high_date_dt
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 20

    def test_price_low_date_dt_property(self) -> None:
        """price_low_date_dt parses date string correctly."""
        stat = HistoricalPriceStatistic(price_low_date="2025-12-01")
        dt = stat.price_low_date_dt
        assert dt is not None
        assert dt.year == 2025
        assert dt.month == 12
        assert dt.day == 1

    def test_dt_properties_return_none_when_date_is_none(self) -> None:
        """_dt properties return None when date string is None."""
        stat = HistoricalPriceStatistic()
        assert stat.period_end_date_dt is None
        assert stat.price_high_date_dt is None
        assert stat.price_low_date_dt is None


class TestVolumeMovingAverage:
    """Tests for the VolumeMovingAverage dataclass."""

    def test_frozen_enforcement(self) -> None:
        """Frozen dataclass rejects attribute assignment."""
        vma = VolumeMovingAverage(value=35904177.91, period="P100D")
        with pytest.raises(AttributeError):
            vma.value = 0.0  # type: ignore[misc]

    def test_from_dict_round_trip(self) -> None:
        """from_dict reconstructs instance from to_dict output."""
        original = VolumeMovingAverage(
            value=35904177.91, period="P100D", period_offset="CURRENT"
        )
        data = original.to_dict()
        reconstructed = VolumeMovingAverage.from_dict(data)
        assert reconstructed.value == 35904177.91
        assert reconstructed.period == "P100D"
        assert reconstructed.period_offset == "CURRENT"

    def test_all_fields_optional(self) -> None:
        """All fields have defaults and can be omitted."""
        vma = VolumeMovingAverage()
        assert vma.value is None
        assert vma.period is None
        assert vma.period_offset is None
