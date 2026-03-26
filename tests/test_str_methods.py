"""Tests for __str__ methods on StockData, WatchlistEntry, FundamentalData, ChartData."""

from __future__ import annotations

import pytest

from tickerscope._models import (
    ChartData,
    DataPoint,
    EstimatePeriod,
    FundamentalData,
    Quote,
    ReportedPeriod,
    TimeSeries,
    WatchlistEntry,
)


# ---------------------------------------------------------------------------
# StockData.__str__
# ---------------------------------------------------------------------------


class TestStockDataStr:
    """Tests for StockData.__str__ output."""

    @pytest.mark.parametrize(
        "expected",
        [
            "AAPL",
            "Apple Inc.",
            "Comp 95",
            "EPS 99",
            "RS 89",
            "SMR A",
            "A/D B+",
            "Computer Software-Desktop",
            "Rank #42",
            "$3.2T",
            "$12.5B",
            "EPS Growth 15.2%",
            "Sales Growth 8.1%",
            "Cup With Handle",
            "Stage 2",
            "$198.45",
        ],
    )
    def test_str_contains(self, full_stock, expected: str) -> None:
        """str(stock_data) includes key field values from the populated model."""
        assert expected in str(full_stock)

    def test_none_fields_handled(self, minimal_stock_empty) -> None:
        """StockData with all-None nested fields shows symbol but omits section labels."""
        output = str(minimal_stock_empty)
        assert "TEST" in output
        assert "Industry:" not in output
        assert "Price:" not in output
        assert "Financials:" not in output
        assert "Pattern:" not in output

    def test_multiline_output(self, full_stock) -> None:
        """Full StockData produces multi-line output."""
        lines = str(full_stock).strip().split("\n")
        assert len(lines) >= 4


# ---------------------------------------------------------------------------
# WatchlistEntry.__str__
# ---------------------------------------------------------------------------


class TestWatchlistEntryStr:
    """Tests for WatchlistEntry.__str__ output."""

    def test_basic(self) -> None:
        """str(entry) includes symbol, name, and price info."""
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
        output = str(entry)
        assert "NVDA" in output
        assert "NVIDIA Corp" in output
        assert "950.50" in output
        assert "Comp 99" in output

    def test_all_none_no_crash(self) -> None:
        """WatchlistEntry with all-None fields doesn't crash on str()."""
        entry = WatchlistEntry(
            symbol=None,
            company_name=None,
            list_rank=None,
            price=None,
            price_net_change=None,
            price_pct_change=None,
            price_pct_off_52w_high=None,
            volume=None,
            volume_change=None,
            volume_pct_change=None,
            composite_rating=None,
            eps_rating=None,
            rs_rating=None,
            acc_dis_rating=None,
            smr_rating=None,
            industry_group_rank=None,
            industry_name=None,
        )
        output = str(entry)
        # Should produce something readable, not crash
        assert isinstance(output, str)
        assert len(output) > 0

    def test_contains_industry(self) -> None:
        """str(entry) includes industry name and rank when present."""
        entry = WatchlistEntry(
            symbol="AAPL",
            company_name="Apple Inc.",
            list_rank=None,
            price=198.45,
            price_net_change=None,
            price_pct_change=1.2,
            price_pct_off_52w_high=None,
            volume=None,
            volume_change=None,
            volume_pct_change=None,
            composite_rating=95,
            eps_rating=99,
            rs_rating=89,
            acc_dis_rating="B+",
            smr_rating="A",
            industry_group_rank=42,
            industry_name="Computer Software-Desktop",
        )
        output = str(entry)
        assert "Computer Software-Desktop" in output
        assert "Rank #42" in output


# ---------------------------------------------------------------------------
# FundamentalData.__str__
# ---------------------------------------------------------------------------


class TestFundamentalDataStr:
    """Tests for FundamentalData.__str__ output."""

    def test_basic(self) -> None:
        """str(fd) shows symbol and period counts."""
        fd = FundamentalData(
            symbol="AAPL",
            company_name="Apple Inc.",
            reported_earnings=[
                ReportedPeriod(
                    value=6.42,
                    formatted_value="$6.42",
                    pct_change_yoy=10.5,
                    formatted_pct_change="10.5%",
                    period_offset="0",
                    period_end_date="2024-12-31",
                ),
                ReportedPeriod(
                    value=5.81,
                    formatted_value="$5.81",
                    pct_change_yoy=8.2,
                    formatted_pct_change="8.2%",
                    period_offset="-1",
                    period_end_date="2023-12-31",
                ),
            ],
            reported_sales=[],
            eps_estimates=[
                EstimatePeriod(
                    value=7.10,
                    formatted_value="$7.10",
                    pct_change_yoy=10.6,
                    formatted_pct_change="10.6%",
                    period_offset="1",
                    period=None,
                    revision_direction="UP",
                ),
            ],
            sales_estimates=[],
        )
        output = str(fd)
        assert "AAPL" in output
        assert "Reported periods: 2" in output
        assert "$6.42" in output
        assert "Estimated periods: 1" in output

    def test_empty_lists(self) -> None:
        """FundamentalData with empty lists shows 'No data'."""
        fd = FundamentalData(
            symbol="XYZ",
            company_name=None,
            reported_earnings=[],
            reported_sales=[],
            eps_estimates=[],
            sales_estimates=[],
        )
        output = str(fd)
        assert "XYZ" in output
        assert "No data" in output


# ---------------------------------------------------------------------------
# ChartData.__str__
# ---------------------------------------------------------------------------


class TestChartDataStr:
    """Tests for ChartData.__str__ output."""

    def test_basic(self) -> None:
        """str(cd) shows symbol and data point count."""
        cd = ChartData(
            symbol="AAPL",
            benchmark_time_series=None,
            time_series=TimeSeries(
                period="P1D",
                data_points=[
                    DataPoint(
                        start_date_time="2024-01-02",
                        end_date_time="2024-01-02",
                        open=185.0,
                        high=186.5,
                        low=184.0,
                        close=185.50,
                        volume=55200000,
                    ),
                    DataPoint(
                        start_date_time="2024-12-31",
                        end_date_time="2024-12-31",
                        open=198.0,
                        high=199.0,
                        low=197.5,
                        close=198.45,
                        volume=42100000,
                    ),
                ],
            ),
            quote=Quote(
                trade_date_time="2024-12-31T16:00:00",
                timeliness=None,
                quote_type=None,
                last=198.45,
                volume=42100000,
                percent_change=0.5,
                net_change=1.0,
            ),
            premarket_quote=None,
            postmarket_quote=None,
            current_market_state=None,
            exchange=None,
        )
        output = str(cd)
        assert "AAPL" in output
        assert "Points: 2" in output
        assert "198.45" in output

    def test_no_time_series(self) -> None:
        """ChartData with no time series shows fallback message."""
        cd = ChartData(
            symbol="XYZ",
            benchmark_time_series=None,
            time_series=None,
            quote=None,
            premarket_quote=None,
            postmarket_quote=None,
            current_market_state=None,
            exchange=None,
        )
        output = str(cd)
        assert "XYZ" in output
        assert "No time series data" in output

    def test_date_range(self) -> None:
        """str(cd) shows the date range from first to last data point."""
        cd = ChartData(
            symbol="MSFT",
            benchmark_time_series=None,
            time_series=TimeSeries(
                period="P1D",
                data_points=[
                    DataPoint(
                        start_date_time="2024-01-02",
                        end_date_time="2024-01-02",
                        open=375.0,
                        high=377.0,
                        low=374.0,
                        close=376.50,
                        volume=30000000,
                    ),
                    DataPoint(
                        start_date_time="2024-06-30",
                        end_date_time="2024-06-30",
                        open=450.0,
                        high=452.0,
                        low=449.0,
                        close=451.25,
                        volume=25000000,
                    ),
                ],
            ),
            quote=None,
            premarket_quote=None,
            postmarket_quote=None,
            current_market_state=None,
            exchange=None,
        )
        output = str(cd)
        assert "2024-01-02" in output
        assert "2024-06-30" in output
