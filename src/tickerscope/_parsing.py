"""Response parsing functions for TickerScope API responses."""

from __future__ import annotations

import datetime
import json
import logging

from tickerscope._exceptions import APIError, SymbolNotFoundError
from tickerscope._models import (
    AdhocScreenResult,
    AlertCriteria,
    CoachTreeData,
    AlertInstrument,
    AlertSubscription,
    AlertSubscriptionList,
    AlertTerm,
    BasicOwnership,
    ChartData,
    ChartMarkup,
    ChartMarkupList,
    Company,
    CorporateActions,
    DataPoint,
    DeliveryPreference,
    Dividend,
    EstimatePeriod,
    ExchangeHoliday,
    ExchangeInfo,
    Financials,
    FundamentalData,
    Fundamentals,
    Industry,
    Layout,
    LayoutColumn,
    NavTreeFolder,
    NavTreeLeaf,
    NavTreeNode,
    AscendingBasePattern,
    CupPattern,
    DoubleBottomPattern,
    IpoBasePattern,
    OwnershipData,
    Panel,
    Pattern,
    PricePercentChanges,
    QuarterlyEstimate,
    QuarterlyFinancials,
    QuarterlyProfitMargin,
    QuarterlyReportedPeriod,
    RSRatingHistory,
    RSRatingSnapshot,
    TightArea,
    Pricing,
    QuarterlyFundOwnership,
    Ratings,
    ReportInfo,
    ReportedPeriod,
    Screen,
    ScreenResult,
    ScreenSource,
    StockData,
    Quote,
    TimeSeries,
    TriggeredAlert,
    TriggeredAlertList,
    TriggeredAlertTerm,
    WatchlistDetail,
    WatchlistEntry,
    WatchlistSymbol,
    WatchlistSummary,
)

_log = logging.getLogger("tickerscope")


def _first(items: list[dict] | None) -> dict:
    """Return the first item in a list-like API field, or empty dict."""
    return items[0] if items else {}


def _safe_value(node: dict | None, key: str = "value"):
    """Safely read nested values from GraphQL scalar wrapper dicts."""
    if not isinstance(node, dict):
        return None
    return node.get(key)


def _safe_date_value(node: dict | None, key: str = "value") -> str | None:
    """Safely read a date string, converting the '0001-01-01' sentinel to None."""
    result = _safe_value(node, key)
    if result == "0001-01-01":
        return None
    return result


def _as_map(items: list[dict], key: str) -> dict:
    """Convert a list of dicts to a lookup dict keyed by `key`."""
    result: dict = {}
    for item in items:
        map_key = item.get(key)
        if map_key:
            result[map_key] = item
    return result


def _to_int(value) -> int | None:
    """Convert a value to int, returning None on conversion failure."""
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_float(value) -> float | None:
    """Convert a value to float, returning None on conversion failure."""
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


_CUP_PATTERN_TYPES = frozenset(
    {
        "CUP_WITH_HANDLE",
        "CUP_WITHOUT_HANDLE",
        "SAUCER_WITH_HANDLE",
        "SAUCER_WITHOUT_HANDLE",
    }
)


def _base_pattern_kwargs(raw: dict) -> dict:
    """Extract common Pattern fields shared by all pattern types."""
    pattern_type = str(raw.get("patternType", "")).replace("_", " ").title()
    return {
        "id": raw.get("id"),
        "pattern_type": pattern_type,
        "periodicity": raw.get("periodicity"),
        "base_stage": raw.get("baseStage"),
        "base_number": raw.get("baseNumber"),
        "base_status": raw.get("baseStatus"),
        "base_length": raw.get("baseLength"),
        "base_depth": _safe_value(raw.get("baseDepth")),
        "base_depth_formatted": _safe_value(raw.get("baseDepth"), "formattedValue"),
        "base_start_date": _safe_date_value(raw.get("baseStartDate")),
        "base_end_date": _safe_date_value(raw.get("baseEndDate")),
        "base_bottom_date": _safe_date_value(raw.get("baseBottomDate")),
        "left_side_high_date": _safe_date_value(raw.get("leftSideHighDate")),
        "pivot_price": _safe_value(raw.get("pivotPrice")),
        "pivot_price_formatted": _safe_value(raw.get("pivotPrice"), "formattedValue"),
        "pivot_date": _safe_date_value(raw.get("pivotDate")),
        "pivot_price_date": _safe_date_value(raw.get("pivotPriceDate")),
        "avg_volume_rate_pct_on_pivot": _safe_value(raw.get("avgVolumeRatePctOnPivot")),
        "avg_volume_rate_pct_on_pivot_formatted": _safe_value(
            raw.get("avgVolumeRatePctOnPivot"), "formattedValue"
        ),
        "price_pct_change_on_pivot": _safe_value(raw.get("pricePctChangeOnPivot")),
        "price_pct_change_on_pivot_formatted": _safe_value(
            raw.get("pricePctChangeOnPivot"), "formattedValue"
        ),
    }


def _build_pattern(raw: dict) -> Pattern:
    """Dispatch a raw pattern dict to the correct Pattern subclass."""
    base = _base_pattern_kwargs(raw)
    ptype = raw.get("patternType", "")

    if ptype in _CUP_PATTERN_TYPES:
        return CupPattern(
            **base,
            handle_depth=_safe_value(raw.get("handleDepth")),
            handle_depth_formatted=_safe_value(
                raw.get("handleDepth"), "formattedValue"
            ),
            handle_length=raw.get("handleLength"),
            cup_length=raw.get("cupLength"),
            cup_end_date=_safe_date_value(raw.get("cupEndDate")),
            handle_low_date=_safe_date_value(raw.get("handleLowDate")),
            handle_start_date=_safe_date_value(raw.get("handleStartDate")),
        )

    if ptype == "DOUBLE_BOTTOM":
        return DoubleBottomPattern(
            **base,
            first_bottom_date=_safe_date_value(raw.get("firstBottomDate")),
            second_bottom_date=_safe_date_value(raw.get("secondBottomDate")),
            mid_peak_date=_safe_date_value(raw.get("midPeakDate")),
        )

    if ptype == "ASCENDING_BASE":
        return AscendingBasePattern(
            **base,
            first_bottom_date=_safe_date_value(raw.get("firstBottomDate")),
            second_ascending_high_date=_safe_date_value(
                raw.get("secondAscendingHighDate")
            ),
            second_bottom_date=_safe_date_value(raw.get("secondBottomDate")),
            third_ascending_high_date=_safe_date_value(
                raw.get("thirdAscendingHighDate")
            ),
            third_bottom_date=_safe_date_value(raw.get("thirdBottomDate")),
            pull_back_1_depth=_safe_value(raw.get("pullBack1Depth")),
            pull_back_1_depth_formatted=_safe_value(
                raw.get("pullBack1Depth"), "formattedValue"
            ),
            pull_back_2_depth=_safe_value(raw.get("pullBack2Depth")),
            pull_back_2_depth_formatted=_safe_value(
                raw.get("pullBack2Depth"), "formattedValue"
            ),
            pull_back_3_depth=_safe_value(raw.get("pullBack3Depth")),
            pull_back_3_depth_formatted=_safe_value(
                raw.get("pullBack3Depth"), "formattedValue"
            ),
        )

    if ptype == "IPO_BASE":
        return IpoBasePattern(
            **base,
            up_bars=raw.get("upBars"),
            blue_bars=raw.get("blueBars"),
            stall_bars=raw.get("stallBars"),
            down_bars=raw.get("downBars"),
            red_bars=raw.get("redBars"),
            support_bars=raw.get("supportBars"),
            up_volume_total=_safe_value(raw.get("upVolumeTotal")),
            up_volume_total_formatted=_safe_value(
                raw.get("upVolumeTotal"), "formattedValue"
            ),
            down_volume_total=_safe_value(raw.get("downVolumeTotal")),
            down_volume_total_formatted=_safe_value(
                raw.get("downVolumeTotal"), "formattedValue"
            ),
            volume_pct_change_on_pivot=_safe_value(raw.get("volumePctChangeOnPivot")),
            volume_pct_change_on_pivot_formatted=_safe_value(
                raw.get("volumePctChangeOnPivot"), "formattedValue"
            ),
        )

    # CONSOLIDATION, FLAT_BASE, and any unknown types use base Pattern
    return Pattern(**base)


def _check_graphql_errors(raw: dict, context: str) -> None:
    """Raise APIError if the GraphQL response contains errors.

    Args:
        raw: The raw GraphQL response dict.
        context: Description of the request for the error message
            (e.g. "symbol 'AAPL'", "watchlist request").
    """
    if raw.get("errors"):
        raise APIError(f"GraphQL errors for {context}", errors=raw["errors"])


def _extract_market_data(raw: dict, symbol: str) -> dict:
    """Extract the first marketData entry from a GraphQL response.

    Args:
        raw: The raw GraphQL response dict.
        symbol: The stock symbol that was queried.

    Raises:
        SymbolNotFoundError: If marketData is empty for the symbol.

    Returns:
        The first dict in the marketData list.
    """
    market_data = raw.get("data", {}).get("marketData", [])
    if not market_data:
        raise SymbolNotFoundError(f"Symbol not found: {symbol!r}", symbol=symbol)
    return market_data[0]


def _build_quarterly_reported(entries: list[dict]) -> list[QuarterlyReportedPeriod]:
    """Build quarterly reported period objects from raw API entries."""
    return [
        QuarterlyReportedPeriod(
            value=_safe_value(e.get("value")),
            pct_change_yoy=_safe_value(e.get("percentChangeYOY")),
            period_offset=e.get("periodOffset", ""),
            period_end_date=_safe_date_value(e.get("periodEndDate")),
            effective_date=_safe_date_value(e.get("effectiveDate")),
            percent_surprise=_safe_value(e.get("percentSurprise")),
            surprise_amount=_safe_value(e.get("surpriseAmount")),
            quarter_number=e.get("quarterNumber"),
            fiscal_year=e.get("fiscalYear"),
        )
        for e in entries
    ]


def _build_quarterly_estimates(entries: list[dict]) -> list[QuarterlyEstimate]:
    """Build quarterly estimate objects from raw API entries."""
    return [
        QuarterlyEstimate(
            value=_safe_value(e.get("value")),
            pct_change_yoy=_safe_value(e.get("percentChangeYOY")),
            period_end_date=_safe_date_value(e.get("periodEndDate")),
            effective_date=_safe_date_value(e.get("effectiveDate")),
            revision_direction=e.get("revisionDirection"),
            estimate_type=e.get("type"),
        )
        for e in entries
    ]


def _build_quarterly_financials(
    eps_consensus: dict, sales_consensus: dict, financials: dict
) -> QuarterlyFinancials:
    """Build QuarterlyFinancials from the OtherMarketData consensus data."""
    estimates = financials.get("estimates", {})
    return QuarterlyFinancials(
        reported_earnings=_build_quarterly_reported(
            eps_consensus.get("reportedEarnings", [])
        ),
        reported_sales=_build_quarterly_reported(
            sales_consensus.get("reportedSales", [])
        ),
        eps_estimates=_build_quarterly_estimates(estimates.get("epsEstimates", [])),
        sales_estimates=_build_quarterly_estimates(estimates.get("salesEstimates", [])),
        profit_margins=[
            QuarterlyProfitMargin(
                period_offset=e.get("periodOffset", ""),
                period_end_date=_safe_date_value(e.get("periodEndDate")),
                pre_tax_margin=_safe_value(e.get("preTaxMargin")),
                after_tax_margin=_safe_value(e.get("afterTaxMargin")),
                gross_margin=_safe_value(e.get("grossMargin")),
                return_on_equity=_safe_value(e.get("returnOnEquity")),
            )
            for e in financials.get("profitMarginValues", [])
        ],
    )


def parse_stock_response(raw: dict, symbol: str) -> StockData:
    """Parse an OtherMarketData GraphQL response into a StockData dataclass.

    Args:
        raw: The raw GraphQL response dict.
        symbol: The stock symbol that was queried.

    Raises:
        APIError: If the response contains GraphQL errors.
        SymbolNotFoundError: If marketData is empty for the symbol.

    Returns:
        StockData with all available fields populated.
    """
    _check_graphql_errors(raw, f"symbol {symbol!r}")
    item = _extract_market_data(raw, symbol)
    ratings = item.get("ratings", {})
    pricing = item.get("pricingStatistics", {})
    pricing_eod = pricing.get("endOfDayStatistics", {})
    pricing_intraday = pricing.get("intradayStatistics", {})
    financials = item.get("financials", {})
    consensus = financials.get("consensusFinancials", {})
    eps_consensus = consensus.get("eps", {})
    sales_consensus = consensus.get("sales", {})
    industry = item.get("industry", {})
    ownership = item.get("ownership", {})
    fundamentals = item.get("fundamentals", {})
    corporate_actions = item.get("corporateActions", {})
    symbology = item.get("symbology", {})

    company = _first(symbology.get("company", []))
    instrument = _first(symbology.get("instrument", []))
    rs_rating = _first(ratings.get("rsRating", []))
    comp_rating = _first(ratings.get("compRating", []))
    eps_rating = _first(ratings.get("epsRating", []))
    smr_rating = _first(ratings.get("smrRating", []))
    ad_rating = _first(ratings.get("adRating", []))

    group_rank = _first(industry.get("groupRanks", []))
    group_rs = _first(industry.get("groupRS", []))

    atr_21d = _first(pricing_eod.get("averageTrueRangePercent", []))
    price_pct_vs = _as_map(pricing_intraday.get("pricePercentChangeVs", []), "subject")
    volume_pct_vs = _as_map(
        pricing_intraday.get("volumePercentChangeVs", []), "subject"
    )

    eps_growth = _first(eps_consensus.get("growthRate", []))
    sales_growth = _first(sales_consensus.get("growthRate", []))
    profit_margin = _first(financials.get("profitMarginValues", []))

    quarterly_financials = _build_quarterly_financials(
        eps_consensus, sales_consensus, financials
    )

    pattern_info = item.get("patternInfo", {})
    pattern_rows: list[Pattern] = [
        _build_pattern(p) for p in pattern_info.get("patterns", [])
    ]
    tight_area_rows: list[TightArea] = [
        TightArea(
            pattern_id=ta.get("patternID"),
            start_date=_safe_date_value(ta.get("startDate")),
            end_date=_safe_date_value(ta.get("endDate")),
            length=ta.get("length"),
        )
        for ta in pattern_info.get("tightAreas", [])
    ]

    return StockData(
        symbol=symbol,
        ratings=Ratings(
            composite=comp_rating.get("value"),
            eps=eps_rating.get("value"),
            rs=rs_rating.get("value"),
            smr=smr_rating.get("letterValue"),
            ad=ad_rating.get("letterValue"),
        ),
        company=Company(
            name=company.get("companyName"),
            industry=industry.get("name"),
            sector=industry.get("sector"),
            industry_group_rank=group_rank.get("value"),
            industry_group_rs=group_rs.get("value"),
            industry_group_rs_letter=group_rs.get("letterValue"),
            description=company.get("businessDescription"),
            website=company.get("url"),
            address=company.get("address"),
            address2=company.get("address2"),
            phone=company.get("phone"),
            ipo_date=_safe_date_value(instrument.get("ipoDate")),
            ipo_price=_safe_value(instrument.get("ipoPrice")),
            ipo_price_formatted=_safe_value(
                instrument.get("ipoPrice"), "formattedValue"
            ),
        ),
        pricing=Pricing(
            market_cap=_safe_value(pricing_eod.get("marketCapitalization")),
            market_cap_formatted=_safe_value(
                pricing_eod.get("marketCapitalization"), "formattedValue"
            ),
            avg_dollar_volume_50d=_safe_value(pricing_eod.get("avgDollarVolume50Day")),
            avg_dollar_volume_50d_formatted=_safe_value(
                pricing_eod.get("avgDollarVolume50Day"), "formattedValue"
            ),
            up_down_volume_ratio=_safe_value(pricing_eod.get("upDownVolumeRatio")),
            up_down_volume_ratio_formatted=_safe_value(
                pricing_eod.get("upDownVolumeRatio"), "formattedValue"
            ),
            atr_percent_21d=_safe_value(atr_21d),
            atr_percent_21d_formatted=_safe_value(atr_21d, "formattedValue"),
            short_interest_percent_float=_safe_value(
                pricing_eod.get("shortInterest", {}).get("percentOfFloat")
            ),
            short_interest_percent_float_formatted=_safe_value(
                pricing_eod.get("shortInterest", {}).get("percentOfFloat"),
                "formattedValue",
            ),
            blue_dot_daily_dates=[
                _safe_value(event)
                for event in pricing_eod.get("blueDotDailyEvents", [])
            ],
            blue_dot_weekly_dates=[
                _safe_value(event)
                for event in pricing_eod.get("blueDotWeeklyEvents", [])
            ],
            ant_dates=[
                _safe_value(event) for event in pricing_eod.get("antEvents", [])
            ],
            price_percent_changes=PricePercentChanges(
                ytd=_safe_value(price_pct_vs.get("VS_YTD", {})),
                mtd=_safe_value(price_pct_vs.get("VS_MTD", {})),
                qtd=_safe_value(price_pct_vs.get("VS_QTD", {})),
                wtd=_safe_value(price_pct_vs.get("VS_WTD", {})),
                vs_1d=_safe_value(price_pct_vs.get("VS_1D_AGO", {})),
                vs_1m=_safe_value(price_pct_vs.get("VS_1M_AGO", {})),
                vs_3m=_safe_value(price_pct_vs.get("VS_3M_AGO", {})),
                vs_year_high=_safe_value(price_pct_vs.get("VS_YEAR_HIGH", {})),
                vs_year_low=_safe_value(price_pct_vs.get("VS_YEAR_LOW", {})),
                vs_5d=_safe_value(price_pct_vs.get("VS_5D_AGO", {})),
                vs_sp500_26w=_safe_value(price_pct_vs.get("VS_SP500_26W_AGO", {})),
                vs_ma10d=_safe_value(price_pct_vs.get("VS_MA10D", {})),
                vs_ma21d=_safe_value(price_pct_vs.get("VS_MA21D", {})),
                vs_ma50d=_safe_value(price_pct_vs.get("VS_MA50D", {})),
                vs_ma150d=_safe_value(price_pct_vs.get("VS_MA150D", {})),
                vs_ma200d=_safe_value(price_pct_vs.get("VS_MA200D", {})),
            ),
            volume_percent_change_vs_50d=_safe_value(volume_pct_vs.get("VS_MA50D", {})),
            dividend_yield=_safe_value(pricing_intraday.get("yield")),
            dividend_yield_formatted=_safe_value(
                pricing_intraday.get("yield"), "formattedValue"
            ),
            price_to_cash_flow_ratio=_safe_value(
                pricing_intraday.get("priceToCashFlowRatio")
            ),
            price_to_cash_flow_ratio_formatted=_safe_value(
                pricing_intraday.get("priceToCashFlowRatio"), "formattedValue"
            ),
            forward_price_to_earnings_ratio=_safe_value(
                pricing_intraday.get("forwardPriceToEarningsRatio")
            ),
            forward_price_to_earnings_ratio_formatted=_safe_value(
                pricing_intraday.get("forwardPriceToEarningsRatio"), "formattedValue"
            ),
            price_to_sales_ratio=_safe_value(pricing_intraday.get("priceToSalesRatio")),
            price_to_sales_ratio_formatted=_safe_value(
                pricing_intraday.get("priceToSalesRatio"), "formattedValue"
            ),
            price_to_earnings_ratio=_safe_value(
                pricing_intraday.get("priceToEarningsRatio")
            ),
            price_to_earnings_ratio_formatted=_safe_value(
                pricing_intraday.get("priceToEarningsRatio"), "formattedValue"
            ),
            pe_vs_sp500=_safe_value(pricing_intraday.get("priceToEarningsVsSP500")),
            pe_vs_sp500_formatted=_safe_value(
                pricing_intraday.get("priceToEarningsVsSP500"), "formattedValue"
            ),
        ),
        financials=Financials(
            eps_due_date=_safe_date_value(financials.get("epsDueDate")),
            eps_due_date_status=financials.get("epsDueDateStatus"),
            eps_last_reported_date=_safe_date_value(
                financials.get("epsLastReportedDate")
            ),
            eps_growth_rate=_safe_value(eps_growth),
            sales_growth_rate_3y=_safe_value(sales_growth),
            pre_tax_margin=_safe_value(profit_margin.get("preTaxMargin")),
            after_tax_margin=_safe_value(profit_margin.get("afterTaxMargin")),
            gross_margin=_safe_value(profit_margin.get("grossMargin")),
            return_on_equity=_safe_value(profit_margin.get("returnOnEquity")),
            earnings_stability=eps_consensus.get("earningsStability"),
        ),
        corporate_actions=CorporateActions(
            next_ex_dividend_date=_safe_value(
                corporate_actions.get("dividendNextReportedExDate")
            ),
            dividends=[
                Dividend(
                    ex_date=_safe_date_value(dividend.get("exDate")),
                    amount=_safe_value(dividend.get("amount"), "formattedValue"),
                    change_indicator=dividend.get("changeIndicator"),
                )
                for dividend in corporate_actions.get("dividends", [])
            ],
            splits=[
                _safe_date_value(split.get("splitDate"))
                for split in corporate_actions.get("splits", [])
            ],
            spinoffs=corporate_actions.get("spinoffs", []),
        ),
        industry=Industry(
            name=industry.get("name"),
            sector=industry.get("sector"),
            code=industry.get("indCode"),
            number_of_stocks=industry.get("numberOfStocksInGroup"),
        ),
        ownership=BasicOwnership(
            funds_float_pct=_safe_value(ownership.get("fundsFloatPercentHeld")),
            funds_float_pct_formatted=_safe_value(
                ownership.get("fundsFloatPercentHeld"), "formattedValue"
            ),
        ),
        fundamentals=Fundamentals(
            r_and_d_percent_last_qtr=_safe_value(
                fundamentals.get("researchAndDevelopmentPercentLastQtr")
            ),
            r_and_d_percent_last_qtr_formatted=_safe_value(
                fundamentals.get("researchAndDevelopmentPercentLastQtr"),
                "formattedValue",
            ),
            debt_percent_formatted=_safe_value(
                fundamentals.get("debtPercent"), "formattedValue"
            ),
            new_ceo_date=_safe_date_value(fundamentals.get("newCEODate")),
        ),
        quarterly_financials=quarterly_financials,
        patterns=pattern_rows,
        tight_areas=tight_area_rows,
    )


def parse_watchlist_response(raw: dict) -> list[WatchlistEntry]:
    """Parse a MarketDataAdhocScreen response into watchlist entries.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        A list of WatchlistEntry rows, or an empty list when no data is present.
    """
    result = parse_adhoc_screen_response(raw)
    return result.entries


def parse_adhoc_screen_response(raw: dict) -> AdhocScreenResult:
    """Parse a MarketDataAdhocScreen response into an AdhocScreenResult.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        AdhocScreenResult with entries and optional error_values.
    """
    _check_graphql_errors(raw, "adhoc screen request")

    adhoc_data = raw.get("data", {}).get("marketDataAdhocScreen", {})
    response_values = adhoc_data.get("responseValues", [])
    error_values = adhoc_data.get("errorValues")

    rows: list[WatchlistEntry] = []
    for row_values in response_values:
        row = {
            col.get("mdItem", {}).get("name", ""): col.get("value")
            for col in row_values
        }
        rows.append(
            WatchlistEntry(
                symbol=row.get("Symbol"),
                company_name=row.get("CompanyName"),
                list_rank=_to_int(row.get("ListRank")),
                price=_to_float(row.get("Price")),
                price_net_change=_to_float(
                    row.get("PriceNetChange", row.get("PriceNetChg"))
                ),
                price_pct_change=_to_float(row.get("PricePctChg")),
                price_pct_off_52w_high=_to_float(row.get("PricePctOff52WHigh")),
                volume=_to_int(row.get("Volume", row.get("VolumeAvg50Day"))),
                volume_change=_to_int(row.get("VolumeChange")),
                volume_pct_change=_to_float(
                    row.get("VolumePctChg", row.get("VolumePctChgVs50DAvgVolume"))
                ),
                composite_rating=_to_int(row.get("CompositeRating")),
                eps_rating=_to_int(row.get("EPSRating")),
                rs_rating=_to_int(row.get("RSRating")),
                acc_dis_rating=row.get("AccDisRating"),
                smr_rating=row.get("SMRRating"),
                industry_group_rank=_to_int(row.get("IndustryGroupRank")),
                industry_name=row.get("IndustryName"),
                market_cap=_to_float(row.get("MarketCapIntraday")),
                volume_dollar_avg_50d=_to_float(row.get("VolumeDollarAvg50D")),
                ipo_date=row.get("IPODate"),
                dow_jones_key=row.get("DowJonesKey"),
                charting_symbol=row.get("ChartingSymbol"),
                instrument_type=row.get("DowJonesInstrumentType"),
                instrument_sub_type=row.get("DowJonesInstrumentSubType"),
            )
        )

    return AdhocScreenResult(entries=rows, error_values=error_values)


def parse_ownership_response(raw: dict, symbol: str) -> OwnershipData:
    """Parse an Ownership GraphQL response into an OwnershipData dataclass.

    Args:
        raw: The raw GraphQL response dict.
        symbol: The stock symbol that was queried.

    Raises:
        APIError: If the response contains GraphQL errors.
        SymbolNotFoundError: If marketData is empty for the symbol.

    Returns:
        OwnershipData with funds-float percentage and quarterly fund history.
    """
    _check_graphql_errors(raw, f"symbol {symbol!r}")
    item = _extract_market_data(raw, symbol)
    ownership = item.get("ownership", {})
    quarterly = ownership.get("fundOwnershipSummary", [])

    return OwnershipData(
        symbol=symbol,
        funds_float_pct=_safe_value(
            ownership.get("fundsFloatPercentHeld"), "formattedValue"
        ),
        quarterly_funds=[
            QuarterlyFundOwnership(
                date=_safe_date_value(item.get("date")),
                count=_safe_value(item.get("numberOfFundsHeld"), "formattedValue"),
            )
            for item in quarterly
        ],
    )


def parse_rs_rating_history_response(raw: dict, symbol: str) -> RSRatingHistory:
    """Parse an RSRatingRIPanel GraphQL response into an RSRatingHistory dataclass.

    Args:
        raw: The raw GraphQL response dict.
        symbol: The stock symbol that was queried.

    Raises:
        APIError: If the response contains GraphQL errors.
        SymbolNotFoundError: If marketData is empty for the symbol.

    Returns:
        RSRatingHistory with RS rating snapshots and rsLineNewHigh flag.
    """
    _check_graphql_errors(raw, f"symbol {symbol!r}")
    item = _extract_market_data(raw, symbol)
    ratings_list = item.get("ratings", {}).get("rsRating", [])
    intraday_stats = item.get("pricingStatistics", {}).get("intradayStatistics", {})

    return RSRatingHistory(
        symbol=symbol,
        ratings=[
            RSRatingSnapshot(
                letter_value=rating.get("letterValue"),
                period=rating.get("period"),
                period_offset=rating.get("periodOffset"),
                value=rating.get("value"),
            )
            for rating in ratings_list
        ],
        rs_line_new_high=intraday_stats.get("rsLineNewHigh"),
    )


def parse_watchlists_response(raw: dict) -> list[WatchlistSummary]:
    """Parse a GetAllWatchlistNames GraphQL response into WatchlistSummary list.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        List of WatchlistSummary, or empty list when no watchlists exist.
    """
    _check_graphql_errors(raw, "watchlist names request")

    items = raw.get("data", {}).get("watchlists", []) or []
    return [
        WatchlistSummary(
            id=_to_int(item.get("id")),
            name=item.get("name"),
            last_modified=item.get("lastModifiedDateUtc"),
            description=item.get("description"),
        )
        for item in items
    ]


def parse_screens_response(raw: dict) -> list[Screen]:
    """Parse a Screens GraphQL response into a list of Screen dataclasses.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        List of Screen objects, or empty list when no screens exist.
    """
    _check_graphql_errors(raw, "screens request")

    items = raw.get("data", {}).get("user", {}).get("screens", []) or []
    screens: list[Screen] = []
    for item in items:
        raw_source = item.get("source")
        source = (
            ScreenSource(
                id=raw_source.get("id"),
                type=raw_source.get("type"),
                pub=raw_source.get("pub"),
            )
            if raw_source
            else None
        )
        screens.append(
            Screen(
                id=item.get("id"),
                name=item.get("name"),
                type=item.get("type"),
                source=source,
                description=item.get("description"),
                filter_criteria=item.get("filterCriteria"),
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt"),
            )
        )
    return screens


def parse_panels_response(raw: dict) -> list[Panel]:
    """Parse an AllPanels GraphQL response into a list of Panel dataclasses.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        List of Panel objects, or empty list when no panels exist.
    """
    _check_graphql_errors(raw, "panels request")

    items = raw.get("data", {}).get("user", {}).get("panels", []) or []
    panels: list[Panel] = []
    for item in items:
        panels.append(
            Panel(
                id=item.get("id"),
                name=item.get("name"),
                site=item.get("site"),
                panel_type=item.get("type"),
                data=item.get("data"),
                created_at=item.get("createdAt"),
                updated_at=item.get("updatedAt"),
            )
        )
    return panels


def _build_nav_tree_node(raw: dict) -> NavTreeNode:
    """Dispatch a raw nav tree dict to NavTreeFolder or NavTreeLeaf."""
    common = {
        "id": raw.get("id"),
        "name": raw.get("name"),
        "parent_id": raw.get("parentId"),
        "node_type": raw.get("type"),
        "tree_type": raw.get("treeType"),
    }

    if "children" in raw:
        return NavTreeFolder(
            **common,
            children=[_build_nav_tree_node(child) for child in raw["children"]],
            content_type=raw.get("contentType"),
        )

    ref_watchlist_id: str | None = None
    ref_screen_id: str | None = None
    ref_original_id: int | None = None
    ref_id = raw.get("referenceId")
    if ref_id:
        try:
            ref = json.loads(ref_id)
            ref_watchlist_id = ref.get("watchlistId")
            ref_screen_id = ref.get("screenId")
            ref_original_id = ref.get("originalId")
        except (json.JSONDecodeError, TypeError):
            _log.debug("Skipping malformed referenceId: %s", ref_id)

    return NavTreeLeaf(
        **common,
        url=raw.get("url"),
        reference_id=ref_id,
        reference_watchlist_id=ref_watchlist_id,
        reference_screen_id=ref_screen_id,
        reference_original_id=ref_original_id,
    )


def parse_nav_tree_response(raw: dict) -> list[NavTreeNode]:
    """Parse a NavTree GraphQL response into a list of NavTreeNode objects.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        List of NavTreeNode (folders and leaves), or empty list when no nodes exist.
    """
    _check_graphql_errors(raw, "nav tree request")

    items = raw.get("data", {}).get("user", {}).get("navTree", []) or []
    return [_build_nav_tree_node(node) for node in items]


def parse_reports_from_nav_tree(nodes: list[NavTreeNode]) -> list[ReportInfo]:
    """Extract predefined report metadata from parsed NavTree nodes.

    Walks the tree recursively and returns a ReportInfo for each
    REPORTS_SCREEN leaf that has an originalId in its referenceId JSON.

    Args:
        nodes: Parsed NavTree nodes from parse_nav_tree_response.

    Returns:
        Deduplicated list of ReportInfo sorted by original_id.
    """
    seen: dict[int, ReportInfo] = {}

    def _collect(items: list[NavTreeNode]) -> None:
        for node in items:
            if isinstance(node, NavTreeFolder):
                _collect(node.children)
            elif (
                isinstance(node, NavTreeLeaf)
                and node.node_type == "REPORTS_SCREEN"
                and node.reference_original_id is not None
                and node.name is not None
            ):
                seen.setdefault(
                    node.reference_original_id,
                    ReportInfo(
                        name=node.name,
                        original_id=node.reference_original_id,
                    ),
                )

    _collect(nodes)
    return sorted(seen.values(), key=lambda r: r.original_id)


def parse_coach_tree_response(raw: dict) -> CoachTreeData:
    """Parse a CoachTree GraphQL response into a CoachTreeData dataclass.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        CoachTreeData with watchlists and screens lists.
    """
    _check_graphql_errors(raw, "coach tree")
    user = raw.get("data", {}).get("user", {})
    watchlists = [_build_nav_tree_node(n) for n in user.get("watchlists", []) or []]
    screens = [_build_nav_tree_node(n) for n in user.get("screens", []) or []]
    return CoachTreeData(watchlists=watchlists, screens=screens)


def parse_watchlist_detail_response(raw: dict, watchlist_id: str) -> WatchlistDetail:
    """Parse a FlaggedSymbols GraphQL response into a WatchlistDetail dataclass.

    Args:
        raw: The raw GraphQL response dict.
        watchlist_id: The watchlist ID that was queried (used in error messages).

    Raises:
        APIError: If the response contains GraphQL errors or watchlist is not found.

    Returns:
        WatchlistDetail with all items populated.
    """
    _check_graphql_errors(raw, f"watchlist {watchlist_id!r}")

    watchlist = raw.get("data", {}).get("watchlist")
    if not watchlist:
        raise APIError(f"Watchlist not found: {watchlist_id!r}")

    return WatchlistDetail(
        id=watchlist.get("id"),
        name=watchlist.get("name"),
        last_modified=watchlist.get("lastModifiedDateUtc"),
        description=watchlist.get("description"),
        items=[
            WatchlistSymbol(
                key=item.get("key"),
                dow_jones_key=item.get("dowJonesKey"),
            )
            for item in watchlist.get("items", [])
        ],
    )


def parse_screen_result_response(raw: dict) -> ScreenResult:
    """Parse a MarketDataScreen GraphQL response into a ScreenResult dataclass.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors or data is missing.

    Returns:
        ScreenResult with metadata and dynamic row data.
    """
    _check_graphql_errors(raw, "screen result request")

    screen_data = raw.get("data", {}).get("marketDataScreen")
    if not screen_data:
        raise APIError("No screen result data returned")

    rows: list[dict[str, str | None]] = [
        {col.get("mdItem", {}).get("name", ""): col.get("value") for col in row_values}
        for row_values in screen_data.get("responseValues", [])
    ]

    return ScreenResult(
        screen_name=screen_data.get("screenName"),
        elapsed_time=screen_data.get("elapsedTime"),
        num_instruments=screen_data.get("numberOfInstrumentsInSource"),
        rows=rows,
    )


def parse_chart_data_response(raw: dict, symbol: str) -> ChartData:
    """Parse a ChartMarketData GraphQL response into a ChartData dataclass.

    Args:
        raw: The raw GraphQL response dict.
        symbol: The stock symbol that was queried.

    Raises:
        APIError: If the response contains GraphQL errors.
        SymbolNotFoundError: If marketData is empty for the symbol.

    Returns:
        ChartData with available chart/time-series fields populated.
    """
    _check_graphql_errors(raw, f"symbol {symbol!r}")
    item = _extract_market_data(raw, symbol)
    pricing = item.get("pricing", {})
    raw_time_series = pricing.get("timeSeries")

    def _parse_quote(raw_quote: dict | None) -> Quote | None:
        if not raw_quote:
            return None

        return Quote(
            trade_date_time=raw_quote.get("tradeDateTime"),
            timeliness=raw_quote.get("timeliness"),
            quote_type=raw_quote.get("quoteType"),
            last=_to_float(_safe_value(raw_quote.get("last"))),
            volume=_to_float(_safe_value(raw_quote.get("volume"))),
            percent_change=_to_float(_safe_value(raw_quote.get("percentChange"))),
            net_change=_to_float(_safe_value(raw_quote.get("netChange"))),
            last_formatted=_safe_value(raw_quote.get("last"), "formattedValue"),
            volume_formatted=_safe_value(raw_quote.get("volume"), "formattedValue"),
            percent_change_formatted=_safe_value(
                raw_quote.get("percentChange"), "formattedValue"
            ),
            net_change_formatted=_safe_value(
                raw_quote.get("netChange"), "formattedValue"
            ),
        )

    time_series = None
    if raw_time_series:
        time_series = TimeSeries(
            period=raw_time_series.get("period", ""),
            data_points=[
                DataPoint(
                    start_date_time=str(data_point.get("startDateTime", "")),
                    end_date_time=str(data_point.get("endDateTime", "")),
                    open=_to_float(_safe_value(data_point.get("open"))),
                    high=_to_float(_safe_value(data_point.get("high"))),
                    low=_to_float(_safe_value(data_point.get("low"))),
                    close=_to_float(_safe_value(data_point.get("last"))),
                    volume=_to_float(_safe_value(data_point.get("volume"))),
                )
                for data_point in raw_time_series.get("dataPoints", [])
            ],
        )

    exchange_data = raw.get("data", {}).get("exchangeData")
    exchange_item = {}
    if isinstance(exchange_data, list):
        exchange_item = _first(exchange_data)
    elif isinstance(exchange_data, dict):
        exchange_item = exchange_data

    exchange = None
    if exchange_item:
        exchange = ExchangeInfo(
            city=exchange_item.get("city"),
            country_code=exchange_item.get("countryCode"),
            exchange_iso=exchange_item.get("exchangeISO"),
            holidays=[
                ExchangeHoliday(
                    name=holiday.get("name", ""),
                    holiday_type=holiday.get("holidayType"),
                    description=holiday.get("description"),
                    start_date_time=str(holiday.get("startDateTime", "")),
                    end_date_time=str(holiday.get("endDateTime", "")),
                )
                for holiday in exchange_item.get("holidays", [])
            ],
        )

    benchmark_time_series = None
    all_market_data = raw.get("data", {}).get("marketData", [])
    if len(all_market_data) > 1:
        bench_pricing = all_market_data[1].get("pricing", {})
        bench_raw_ts = bench_pricing.get("timeSeries")
        if bench_raw_ts:
            benchmark_time_series = TimeSeries(
                period=bench_raw_ts.get("period", ""),
                data_points=[
                    DataPoint(
                        start_date_time=str(dp.get("startDateTime", "")),
                        end_date_time=str(dp.get("endDateTime", "")),
                        open=_to_float(_safe_value(dp.get("open"))),
                        high=_to_float(_safe_value(dp.get("high"))),
                        low=_to_float(_safe_value(dp.get("low"))),
                        close=_to_float(_safe_value(dp.get("last"))),
                        volume=_to_float(_safe_value(dp.get("volume"))),
                    )
                    for dp in bench_raw_ts.get("dataPoints", [])
                ],
            )

    return ChartData(
        symbol=symbol,
        time_series=time_series,
        benchmark_time_series=benchmark_time_series,
        quote=_parse_quote(pricing.get("quote")),
        premarket_quote=_parse_quote(pricing.get("premarketQuote")),
        postmarket_quote=_parse_quote(pricing.get("postmarketQuote")),
        current_market_state=pricing.get("currentMarketState"),
        exchange=exchange,
    )


def parse_fundamentals_response(raw: dict, symbol: str) -> FundamentalData:
    """Parse a FundermentalDataBox GraphQL response into a FundamentalData dataclass.

    Args:
        raw: The raw GraphQL response dict.
        symbol: The stock symbol that was queried.

    Raises:
        APIError: If the response contains GraphQL errors.
        SymbolNotFoundError: If marketData is empty for the symbol.

    Returns:
        FundamentalData with reported earnings/sales and estimates.
    """
    _check_graphql_errors(raw, f"symbol {symbol!r}")
    item = _extract_market_data(raw, symbol)
    financials = item.get("financials", {})
    consensus = financials.get("consensusFinancials", {})
    estimates = financials.get("estimates", {})
    symbology = item.get("symbology", {})
    company_name = _first(symbology.get("company", [])).get("companyName")

    reported_earnings = [
        ReportedPeriod(
            value=_safe_value(entry.get("value")),
            formatted_value=_safe_value(entry.get("value"), "formattedValue"),
            pct_change_yoy=_safe_value(entry.get("percentChangeYOY")),
            formatted_pct_change=_safe_value(
                entry.get("percentChangeYOY"), "formattedValue"
            ),
            period_offset=entry.get("periodOffset", ""),
            period_end_date=_safe_date_value(entry.get("periodEndDate")),
        )
        for entry in consensus.get("eps", {}).get("reportedEarnings", [])
    ]

    reported_sales = [
        ReportedPeriod(
            value=_safe_value(entry.get("value")),
            formatted_value=_safe_value(entry.get("value"), "formattedValue"),
            pct_change_yoy=_safe_value(entry.get("percentChangeYOY")),
            formatted_pct_change=_safe_value(
                entry.get("percentChangeYOY"), "formattedValue"
            ),
            period_offset=entry.get("periodOffset", ""),
            period_end_date=_safe_date_value(entry.get("periodEndDate")),
        )
        for entry in consensus.get("sales", {}).get("reportedSales", [])
    ]

    eps_estimates = [
        EstimatePeriod(
            value=_safe_value(entry.get("value")),
            formatted_value=_safe_value(entry.get("value"), "formattedValue"),
            pct_change_yoy=_safe_value(entry.get("percentChangeYOY")),
            formatted_pct_change=_safe_value(
                entry.get("percentChangeYOY"), "formattedValue"
            ),
            period_offset=entry.get("periodOffset", ""),
            period=entry.get("period"),
            revision_direction=entry.get("revisionDirection"),
        )
        for entry in estimates.get("epsEstimates", [])
    ]

    sales_estimates = [
        EstimatePeriod(
            value=_safe_value(entry.get("value")),
            formatted_value=_safe_value(entry.get("value"), "formattedValue"),
            pct_change_yoy=_safe_value(entry.get("percentChangeYOY")),
            formatted_pct_change=_safe_value(
                entry.get("percentChangeYOY"), "formattedValue"
            ),
            period_offset=entry.get("periodOffset", ""),
            period=entry.get("period"),
            revision_direction=entry.get("revisionDirection"),
        )
        for entry in estimates.get("salesEstimates", [])
    ]

    return FundamentalData(
        symbol=symbol,
        company_name=company_name,
        reported_earnings=reported_earnings,
        reported_sales=reported_sales,
        eps_estimates=eps_estimates,
        sales_estimates=sales_estimates,
    )


def parse_active_alerts_response(raw: dict) -> AlertSubscriptionList:
    """Parse an ActiveAlerts GraphQL response into an AlertSubscriptionList.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        AlertSubscriptionList with subscriptions and quota counts.
    """
    _check_graphql_errors(raw, "active alerts request")

    container = (
        raw.get("data", {}).get("user", {}).get("followSubscriptionsWithCount", {})
    )

    raw_subs = container.get("subscriptions", [])
    subscriptions: list[AlertSubscription] = []

    for sub in raw_subs:
        delivery_prefs = [
            DeliveryPreference(
                method=pref.get("method", ""),
                type=pref.get("type", ""),
            )
            for pref in sub.get("deliveryPreferences", [])
        ]

        raw_criteria = sub.get("criteria")
        criteria = None
        if raw_criteria:
            raw_term = raw_criteria.get("term")
            term = None
            if raw_term:
                instrument = None
                raw_instrument = raw_term.get("instrumentResult")
                if raw_instrument:
                    instrument = AlertInstrument(
                        djid=raw_instrument.get("djid"),
                        ticker=raw_instrument.get("ticker"),
                        charting_symbol=raw_instrument.get("chartingSymbol"),
                    )
                term = AlertTerm(
                    value=raw_term.get("value"),
                    operator=raw_term.get("operator"),
                    field=raw_term.get("field"),
                    instrument=instrument,
                )

            criteria = AlertCriteria(
                criteria_id=raw_criteria.get("criteriaId", ""),
                engine=raw_criteria.get("engine"),
                product=raw_criteria.get("product"),
                alert_type=raw_criteria.get("alertType"),
                term=term,
            )

        subscriptions.append(
            AlertSubscription(
                delivery_preferences=delivery_prefs,
                criteria=criteria,
                create_date=sub.get("createDate"),
                note=sub.get("note"),
            )
        )

    return AlertSubscriptionList(
        subscriptions=subscriptions,
        num_subscriptions=container.get("numSubscriptions", 0),
        remaining_subscriptions=container.get("remainingSubscriptions", 0),
    )


def parse_triggered_alerts_response(raw: dict) -> TriggeredAlertList:
    """Parse a TriggeredAlerts GraphQL response into a TriggeredAlertList.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        TriggeredAlertList with alerts and cursor.
    """
    _check_graphql_errors(raw, "triggered alerts request")

    container = raw.get("data", {}).get("user", {}).get("followAlerts", {})
    raw_alerts = container.get("alerts", [])
    alerts: list[TriggeredAlert] = []

    for alert in raw_alerts:
        raw_pref = alert.get("deliveryPreferences")
        delivery_preference = (
            DeliveryPreference(
                method=raw_pref.get("method", ""),
                type=raw_pref.get("type", ""),
            )
            if raw_pref
            else None
        )

        raw_term = alert.get("term")
        term = None
        if raw_term:
            instrument = None
            raw_instrument = raw_term.get("instrumentResult")
            if raw_instrument:
                instrument = AlertInstrument(
                    djid=raw_instrument.get("djid"),
                    ticker=raw_instrument.get("ticker"),
                    charting_symbol=raw_instrument.get("chartingSymbol"),
                )
            term = TriggeredAlertTerm(
                value=raw_term.get("value"),
                operator=raw_term.get("operator"),
                field=raw_term.get("field"),
                dj_key=raw_term.get("djKey"),
                instrument=instrument,
            )

        alerts.append(
            TriggeredAlert(
                alert_id=alert.get("alertId", ""),
                alert_type=alert.get("alertType"),
                engine=alert.get("engine"),
                delivery_preference=delivery_preference,
                term=term,
                criteria_id=alert.get("criteriaId"),
                payload=alert.get("payload", {}),
                product=alert.get("product"),
                delivered=bool(alert.get("delivered", False)),
                viewed=bool(alert.get("viewed", False)),
                deleted=bool(alert.get("deleted", False)),
                create_date=alert.get("createDate"),
                ttl=_to_int(alert.get("ttl")),
            )
        )

    return TriggeredAlertList(
        cursor_id=container.get("cursorId"),
        alerts=alerts,
    )


def parse_layouts_response(raw: dict) -> list[Layout]:
    """Parse a MarketDataLayouts GraphQL response into a list of Layout dataclasses.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        List of Layout objects, or empty list when no layouts exist.
    """
    _check_graphql_errors(raw, "layouts request")

    items = raw.get("data", {}).get("user", {}).get("marketDataLayouts", []) or []
    layouts: list[Layout] = []
    for item in items:
        columns = [
            LayoutColumn(
                md_item_id=col.get("mdItemId", ""),
                name=col.get("name", ""),
                width=col.get("width"),
                locked=bool(col.get("locked", False)),
                visible=bool(col.get("visible", False)),
            )
            for col in item.get("columns", [])
        ]
        layouts.append(
            Layout(
                id=item.get("id", ""),
                name=item.get("name", ""),
                site=item.get("site"),
                columns=columns,
            )
        )
    return layouts


def parse_chart_markups_response(raw: dict) -> ChartMarkupList:
    """Parse a FetchChartMarkups GraphQL response into a ChartMarkupList.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        ChartMarkupList with markups and cursor_id.
    """
    _check_graphql_errors(raw, "chart markups request")

    container = raw.get("data", {}).get("user", {}).get("chartMarkups", {})
    raw_markups = container.get("chartMarkups", [])

    markups: list[ChartMarkup] = []
    for markup in raw_markups:
        markups.append(
            ChartMarkup(
                id=markup.get("id", ""),
                name=markup.get("name"),
                data=markup.get("data", ""),
                frequency=markup.get("frequency"),
                site=markup.get("site"),
                created_at=markup.get("createdAt"),
                updated_at=markup.get("updatedAt"),
            )
        )

    return ChartMarkupList(
        cursor_id=container.get("cursorId"),
        markups=markups,
    )


def parse_server_time_response(raw: dict) -> datetime.datetime:
    """Parse GetServerDateTime GraphQL response into a timezone-aware datetime.

    Args:
        raw: GraphQL response dict with ibdGetServerDateTime field.

    Returns:
        Timezone-aware datetime.datetime object.

    Raises:
        APIError: If response contains GraphQL errors or server time is missing.
    """
    _check_graphql_errors(raw, "server time")
    ts = raw.get("data", {}).get("ibdGetServerDateTime")
    if not ts:
        raise APIError("Server returned no datetime", errors=[])
    return datetime.datetime.fromisoformat(ts)
