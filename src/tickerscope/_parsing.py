"""Response parsing functions for TickerScope API responses."""

from __future__ import annotations

import logging

from tickerscope._exceptions import APIError, SymbolNotFoundError
from tickerscope._models import (
    AlertCriteria,
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
    OwnershipData,
    Pattern,
    PricePercentChanges,
    Pricing,
    QuarterlyFundOwnership,
    Ratings,
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
    WatchlistItem,
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
    if raw.get("errors"):
        raise APIError(
            f"GraphQL errors for symbol {symbol!r}",
            errors=raw["errors"],
        )

    market_data = raw.get("data", {}).get("marketData", [])
    if not market_data:
        raise SymbolNotFoundError(f"Symbol not found: {symbol!r}", symbol=symbol)

    item = market_data[0]
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

    pattern_rows: list[Pattern] = []
    for pattern in item.get("patternInfo", {}).get("patterns", []):
        pattern_rows.append(
            Pattern(
                type=str(pattern.get("patternType", "")).replace("_", " ").title(),
                stage=pattern.get("baseStage"),
                base_number=pattern.get("baseNumber"),
                status=pattern.get("baseStatus"),
                pivot_price=_safe_value(pattern.get("pivotPrice")),
                pivot_price_formatted=_safe_value(
                    pattern.get("pivotPrice"), "formattedValue"
                ),
                pivot_date=_safe_value(pattern.get("pivotDate")),
                base_start_date=_safe_value(pattern.get("baseStartDate")),
                base_end_date=_safe_value(pattern.get("baseEndDate")),
                base_length=pattern.get("baseLength"),
            )
        )

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
            ipo_date=_safe_value(instrument.get("ipoDate")),
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
            ),
            volume_percent_change_vs_50d=_safe_value(volume_pct_vs.get("VS_MA50D", {})),
        ),
        financials=Financials(
            eps_due_date=_safe_value(financials.get("epsDueDate")),
            eps_due_date_status=financials.get("epsDueDateStatus"),
            eps_last_reported_date=_safe_value(financials.get("epsLastReportedDate")),
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
                    ex_date=_safe_value(dividend.get("exDate")),
                    amount=_safe_value(dividend.get("amount"), "formattedValue"),
                    change_indicator=dividend.get("changeIndicator"),
                )
                for dividend in corporate_actions.get("dividends", [])
            ],
            splits=[
                _safe_value(split.get("splitDate"))
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
            new_ceo_date=_safe_value(fundamentals.get("newCEODate")),
        ),
        patterns=pattern_rows,
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
    if raw.get("errors"):
        raise APIError("GraphQL errors for watchlist request", errors=raw["errors"])

    response_values = (
        raw.get("data", {}).get("marketDataAdhocScreen", {}).get("responseValues", [])
    )
    if not response_values:
        return []

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
            )
        )

    return rows


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
    if raw.get("errors"):
        raise APIError(
            f"GraphQL errors for symbol {symbol!r}",
            errors=raw["errors"],
        )

    market_data = raw.get("data", {}).get("marketData", [])
    if not market_data:
        _log.debug("No ownership marketData returned for symbol %s", symbol)
        raise SymbolNotFoundError(f"Symbol not found: {symbol!r}", symbol=symbol)

    ownership = market_data[0].get("ownership", {})
    quarterly = ownership.get("fundOwnershipSummary", [])

    return OwnershipData(
        symbol=symbol,
        funds_float_pct=_safe_value(
            ownership.get("fundsFloatPercentHeld"), "formattedValue"
        ),
        quarterly_funds=[
            QuarterlyFundOwnership(
                date=_safe_value(item.get("date")),
                count=_safe_value(item.get("numberOfFundsHeld"), "formattedValue"),
            )
            for item in quarterly
        ],
    )


def parse_watchlist_names_response(raw: dict) -> list[WatchlistSummary]:
    """Parse a GetAllWatchlistNames GraphQL response into WatchlistSummary list.

    Args:
        raw: The raw GraphQL response dict.

    Raises:
        APIError: If the response contains GraphQL errors.

    Returns:
        List of WatchlistSummary, or empty list when no watchlists exist.
    """
    if raw.get("errors"):
        raise APIError(
            "GraphQL errors for watchlist names request", errors=raw["errors"]
        )

    items = raw.get("data", {}).get("watchlists", []) or []
    return [
        WatchlistSummary(
            id=item.get("id"),
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
    if raw.get("errors"):
        raise APIError("GraphQL errors for screens request", errors=raw["errors"])

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
    if raw.get("errors"):
        raise APIError(
            f"GraphQL errors for watchlist {watchlist_id!r}",
            errors=raw["errors"],
        )

    watchlist = raw.get("data", {}).get("watchlist")
    if not watchlist:
        raise APIError(f"Watchlist not found: {watchlist_id!r}")

    return WatchlistDetail(
        id=watchlist.get("id"),
        name=watchlist.get("name"),
        last_modified=watchlist.get("lastModifiedDateUtc"),
        description=watchlist.get("description"),
        items=[
            WatchlistItem(
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
    if raw.get("errors"):
        raise APIError("GraphQL errors for screen result request", errors=raw["errors"])

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
    if raw.get("errors"):
        raise APIError(
            f"GraphQL errors for symbol {symbol!r}",
            errors=raw["errors"],
        )

    market_data = raw.get("data", {}).get("marketData", [])
    if not market_data:
        raise SymbolNotFoundError(f"Symbol not found: {symbol!r}", symbol=symbol)

    item = market_data[0]
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

    return ChartData(
        symbol=symbol,
        time_series=time_series,
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
    if raw.get("errors"):
        raise APIError(
            f"GraphQL errors for symbol {symbol!r}",
            errors=raw["errors"],
        )

    market_data = raw.get("data", {}).get("marketData", [])
    if not market_data:
        raise SymbolNotFoundError(f"Symbol not found: {symbol!r}", symbol=symbol)

    item = market_data[0]
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
            period_end_date=_safe_value(entry.get("periodEndDate")),
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
            period_end_date=_safe_value(entry.get("periodEndDate")),
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
    if raw.get("errors"):
        raise APIError("GraphQL errors for active alerts request", errors=raw["errors"])

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
    if raw.get("errors"):
        raise APIError(
            "GraphQL errors for triggered alerts request", errors=raw["errors"]
        )

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
    if raw.get("errors"):
        raise APIError("GraphQL errors for layouts request", errors=raw["errors"])

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
    if raw.get("errors"):
        raise APIError("GraphQL errors for chart markups request", errors=raw["errors"])

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
