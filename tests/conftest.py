"""Pytest configuration and shared fixtures for MarketSurge tests."""

from __future__ import annotations

# pyright: reportMissingImports=false

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from tickerscope._client import AsyncTickerScopeClient, TickerScopeClient
from tickerscope._models import CupPattern, Pricing, Ratings, StockData

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _json_fixture(filename: str):
    """Create a pytest fixture that loads a JSON file from the fixtures directory."""

    @pytest.fixture(name=filename.removesuffix(".json"))
    def _load():
        with open(FIXTURES_DIR / filename) as f:
            return json.load(f)

    return _load


stock_response = _json_fixture("stock_response.json")
stock_extracted = _json_fixture("stock_extracted.json")
watchlist_names_response = _json_fixture("watchlist_names_response.json")
flagged_symbols_response = _json_fixture("flagged_symbols_response.json")
screens_response = _json_fixture("screens_response.json")
screen_result_response = _json_fixture("screen_result_response.json")
chart_data_response = _json_fixture("chart_data_response.json")
fundamentals_response = _json_fixture("fundamentals_response.json")
active_alerts_response = _json_fixture("active_alerts_response.json")
triggered_alerts_response = _json_fixture("triggered_alerts_response.json")
layouts_response = _json_fixture("layouts_response.json")
chart_markups_response = _json_fixture("chart_markups_response.json")
panels_response = _json_fixture("panels_response.json")
rs_rating_history_response = _json_fixture("rs_rating_history_response.json")
server_time_response = _json_fixture("server_time_response.json")
nav_tree_response = _json_fixture("nav_tree_response.json")


# ---------------------------------------------------------------------------
# Client fixtures
# ---------------------------------------------------------------------------

FAKE_JWT = "fake-jwt"


@pytest.fixture
def sync_client():
    """Create a sync TickerScopeClient with mocked authentication."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = TickerScopeClient()
    yield client
    client.close()


@pytest.fixture
async def async_client():
    """Create an async TickerScopeClient with mocked authentication."""
    with patch("tickerscope._client.resolve_jwt", return_value=FAKE_JWT):
        client = AsyncTickerScopeClient()
    yield client
    await client.aclose()


# ---------------------------------------------------------------------------
# Model builder fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_pricing():
    """Return a factory callable for building Pricing instances with optional overrides."""

    def _build(**overrides: object) -> Pricing:
        defaults: dict = dict(
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
            price_percent_changes=None,
            volume_percent_change_vs_50d=None,
        )
        defaults.update(overrides)
        return Pricing(**defaults)

    return _build


@pytest.fixture
def minimal_stock():
    """Return a factory callable for building StockData with actual ratings, overridable per-field."""

    def _build(**overrides: object) -> StockData:
        defaults: dict = dict(
            symbol="TEST",
            ratings=Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+"),
            company=None,
            pricing=None,
            financials=None,
            corporate_actions=None,
            industry=None,
            ownership=None,
            fundamentals=None,
            patterns=[],
            tight_areas=[],
        )
        defaults.update(overrides)
        return StockData(**defaults)

    return _build


@pytest.fixture
def minimal_stock_empty() -> StockData:
    """Build a StockData with None for all ratings (all-None ratings variant)."""
    return StockData(
        symbol="TEST",
        ratings=Ratings(composite=None, eps=None, rs=None, smr=None, ad=None),
        company=None,
        pricing=None,
        financials=None,
        corporate_actions=None,
        industry=None,
        ownership=None,
        fundamentals=None,
        patterns=[],
        tight_areas=[],
    )


@pytest.fixture
def full_stock() -> StockData:
    """Build a fully-populated StockData for str output tests."""
    from tickerscope._models import (
        BasicOwnership,
        Company,
        CorporateActions,
        Financials,
        Fundamentals,
        Industry,
        PricePercentChanges,
    )

    return StockData(
        symbol="AAPL",
        ratings=Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+"),
        company=Company(
            name="Apple Inc.",
            industry="Computer Software-Desktop",
            sector="Technology",
            industry_group_rank=42,
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
            market_cap=3.2e12,
            market_cap_formatted="$3.2T",
            avg_dollar_volume_50d=1.25e10,
            avg_dollar_volume_50d_formatted="$12.5B",
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
            eps_growth_rate=15.2,
            sales_growth_rate_3y=8.1,
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
            name="Computer Software-Desktop",
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
        patterns=[
            CupPattern(
                id=None,
                pattern_type="Cup With Handle",
                periodicity=None,
                base_stage="2",
                base_number=1,
                base_status="COMPLETE",
                base_depth=None,
                base_depth_formatted=None,
                pivot_price=198.45,
                pivot_price_formatted="$198.45",
                pivot_date="2024-06-15",
                pivot_price_date=None,
                avg_volume_rate_pct_on_pivot=None,
                avg_volume_rate_pct_on_pivot_formatted=None,
                price_pct_change_on_pivot=None,
                price_pct_change_on_pivot_formatted=None,
                base_start_date="2024-01-10",
                base_end_date="2024-06-14",
                base_bottom_date=None,
                left_side_high_date=None,
                base_length=110,
                handle_depth=None,
                handle_depth_formatted=None,
                handle_length=None,
                cup_length=None,
                cup_end_date=None,
                handle_low_date=None,
                handle_start_date=None,
            ),
        ],
        tight_areas=[],
    )
