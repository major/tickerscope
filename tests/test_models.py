"""Tests for frozen dataclass models."""

import pytest

from tickerscope._models import (
    BasicOwnership,
    Company,
    CorporateActions,
    Dividend,
    Financials,
    Fundamentals,
    Industry,
    OwnershipData,
    Pattern,
    PricePercentChanges,
    Pricing,
    Quote,
    QuarterlyFundOwnership,
    Ratings,
    StockData,
    WatchlistEntry,
)


class TestRatings:
    """Tests for the Ratings dataclass."""

    def test_construction(self) -> None:
        """Construct a Ratings instance with typical values."""
        r = Ratings(composite=95, eps=88, rs=92, smr="A", ad="B")
        assert r.composite == 95
        assert r.eps == 88
        assert r.rs == 92
        assert r.smr == "A"
        assert r.ad == "B"

    def test_frozen_enforcement(self) -> None:
        """Frozen dataclass rejects attribute assignment."""
        r = Ratings(composite=95, eps=88, rs=92, smr="A", ad="B")
        with pytest.raises(AttributeError):
            r.composite = 50  # type: ignore[misc]

    def test_all_none(self) -> None:
        """All fields accept None."""
        r = Ratings(composite=None, eps=None, rs=None, smr=None, ad=None)
        assert r.composite is None
        assert r.eps is None
        assert r.rs is None
        assert r.smr is None
        assert r.ad is None


class TestStockData:
    """Tests for the fully nested StockData dataclass."""

    def test_full_construction(self) -> None:
        """Construct a complete StockData with all nested dataclasses."""
        stock = StockData(
            symbol="AAPL",
            ratings=Ratings(composite=95, eps=88, rs=92, smr="A", ad="B"),
            company=Company(
                name="Apple Inc",
                industry="Comp-Peripherals",
                sector="Technology",
                industry_group_rank=5,
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
                market_cap=3000000000000,
                market_cap_formatted="3.0T",
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
            industry=Industry(
                name="Comp-Peripherals",
                sector="Technology",
                code=None,
                number_of_stocks=None,
            ),
            ownership=BasicOwnership(
                funds_float_pct=None,
                funds_float_pct_formatted=None,
            ),
            fundamentals=Fundamentals(
                r_and_d_percent_last_qtr=None,
                r_and_d_percent_last_qtr_formatted=None,
                debt_percent_formatted=None,
                new_ceo_date=None,
            ),
            patterns=[],
        )
        assert stock.ratings.composite == 95
        assert stock.company.name == "Apple Inc"

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
            patterns=[],
        )
        with pytest.raises(AttributeError):
            stock.symbol = "GOOG"  # type: ignore[misc]


class TestWatchlistEntry:
    """Tests for the WatchlistEntry dataclass."""

    def test_construction(self) -> None:
        """Construct a WatchlistEntry with sample data."""
        entry = WatchlistEntry(
            symbol="NVDA",
            company_name="NVIDIA Corp",
            list_rank=1,
            price=950.50,
            price_net_change=12.30,
            price_pct_change=1.31,
            price_pct_off_52w_high=-5.2,
            volume=45000000,
            volume_change=5000000,
            volume_pct_change=12.5,
            composite_rating=99,
            eps_rating=97,
            rs_rating=95,
            acc_dis_rating="A",
            smr_rating="A",
            industry_group_rank=3,
            industry_name="Elec-Semiconductor",
        )
        assert entry.symbol == "NVDA"
        assert entry.company_name == "NVIDIA Corp"
        assert entry.list_rank == 1
        assert entry.composite_rating == 99
        assert entry.acc_dis_rating == "A"
        assert entry.industry_name == "Elec-Semiconductor"


class TestOwnershipData:
    """Tests for OwnershipData with QuarterlyFundOwnership list."""

    def test_construction(self) -> None:
        """Construct OwnershipData with quarterly fund ownership entries."""
        ownership = OwnershipData(
            symbol="AAPL",
            funds_float_pct="43.87%",
            quarterly_funds=[
                QuarterlyFundOwnership(date="2025-12-31", count="245"),
                QuarterlyFundOwnership(date="2025-09-30", count="238"),
                QuarterlyFundOwnership(date="2025-06-30", count="230"),
            ],
        )
        assert ownership.symbol == "AAPL"
        assert ownership.funds_float_pct == "43.87%"
        assert len(ownership.quarterly_funds) == 3
        assert ownership.quarterly_funds[0].date == "2025-12-31"
        assert ownership.quarterly_funds[0].count == "245"


class TestCorporateActions:
    """Tests for CorporateActions with nested Dividend list."""

    def test_with_dividends(self) -> None:
        """Construct CorporateActions containing Dividend instances."""
        ca = CorporateActions(
            next_ex_dividend_date="2026-03-09",
            dividends=[
                Dividend(
                    ex_date="2025-12-08", amount="$0.21", change_indicator="UNKNOWN"
                ),
                Dividend(
                    ex_date="2025-09-08", amount="$0.21", change_indicator="UNKNOWN"
                ),
            ],
            splits=["2014-04-03", "2022-07-18"],
            spinoffs=[],
        )
        assert ca.next_ex_dividend_date == "2026-03-09"
        assert len(ca.dividends) == 2
        assert ca.dividends[0].amount == "$0.21"
        assert ca.splits == ["2014-04-03", "2022-07-18"]


class TestPattern:
    """Tests for the Pattern dataclass."""

    def test_construction(self) -> None:
        """Construct a Pattern with typical values."""
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
        assert p.type == "Cup With Handle"
        assert p.stage == 1
        assert p.base_length == 40


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
