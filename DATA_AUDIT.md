# tickerscope Data Audit

**Date:** 2026-03-26
**Source:** `daily_with_eps.har` (MarketSurge browser session with all panels enabled)
**Method:** Field-by-field comparison of HAR GraphQL traffic vs codebase queries, parsers, and models

## Executive Summary

tickerscope covers all 17 GraphQL operations the browser makes. No missing operations.
The two problems are real, though:

1. **3 fields the browser queries that our `.graphql` files don't** (query gap)
2. **~30 fields we query from the API but silently discard in parsing** (parser/model gap)

The discarded data includes valuation ratios (P/E, P/S, forward P/E), moving average
distances, alpha/beta, full short interest details, dividend yield, cash flow per share,
and historical industry group rankings - all high-value data for stock analysis.

---

## Section 1: Operation Coverage (No Gaps)

Every GraphQL operation in the HAR file exists in the codebase. Two codebase operations
were not triggered during the HAR capture but are valid additional coverage.

```text
 HAR Operation             Codebase .graphql            Status
 -------------------------  ---------------------------  --------
 AllPanels                  all_panels.graphql           MATCH
 ChartMarketData            chart_market_data.graphql    MATCH
 OtherMarketData            other_market_data.graphql    MATCH
 FetchChartMarkups          chart_markups.graphql        MATCH
 FundermentalDataBox        fundamentals.graphql         MATCH
 ActiveAlerts               active_alerts.graphql        MATCH
 TriggeredAlerts            triggered_alerts.graphql     MATCH
 MarketDataScreen           market_data_screen.graphql   MATCH
 Ownership                  ownership.graphql            MATCH
 GetServerDateTime          get_server_date_time.graphql MATCH
 NavTree                    nav_tree.graphql             MATCH
 CoachTree                  coach_tree.graphql           MATCH
 MarketDataLayouts          market_data_layouts.graphql  MATCH
 GetAllWatchlistNames       watchlist_names.graphql      MATCH
 Screens                    screens.graphql              MATCH
 MarketDataAdhocScreen      adhoc_screen.graphql         MATCH
 FlaggedSymbols             flagged_symbols.graphql      MATCH
 (not in HAR)               rs_rating_ri_panel.graphql   EXTRA
 (not in HAR)               chart_market_data_weekly.graphql  EXTRA
```

---

## Section 2: Query Gaps (Fields Browser Requests That We Don't)

These fields appear in the HAR's OtherMarketData query but are absent from
`other_market_data.graphql`. The API returns this data for the browser, but we
never ask for it.

### 2.1 Company Location Fields

The HAR's `symbology.company` selection includes three fields ours does not.

**HAR query:**

```graphql
company {
  companyName
  address
  address2
  city          # MISSING from our query
  country       # MISSING from our query
  stateProvince # MISSING from our query
  phone
  businessDescription
  url
}
```

**Our query (`other_market_data.graphql` line 221-229):**

```graphql
company {
  companyName
  address
  address2
  phone
  businessDescription
  url
}
```

**Impact:** Company model has no city/country/state fields. Users cannot filter or
display company headquarters location.

### 2.2 Watchlist Screen Columns

The HAR's MarketDataAdhocScreen request includes 23 columns. Our `WATCHLIST_COLUMNS`
constant in `_queries.py` requests 17. Six data-carrying columns are never requested.

```text
 HAR Column                   WATCHLIST_COLUMNS  WatchlistEntry Model
 ----------------------------  -----------------  ------------------
 Symbol                        YES                YES
 CompanyName                   YES                YES
 ListRank                      YES                YES
 Price                         YES                YES
 PriceNetChg                   YES                YES
 PricePctChg                   YES                YES
 PricePctOff52WHigh            YES                YES
 VolumePctChgVs50DAvgVolume    YES                YES
 VolumeAvg50Day                YES                YES
 VolumeDollarAvg50D            NO                 NO
 MarketCapIntraday             YES                NO (queried, discarded)
 CompositeRating               YES                YES
 EPSRating                     YES                YES
 RSRating                      YES                YES
 AccDisRating                  YES                YES
 SMRRating                     YES                YES
 IndustryGroupRank             YES                YES
 IndustryName                  YES                YES
 IPODate                       NO                 NO
 DowJonesKey                   NO                 NO
 ChartingSymbol                NO                 NO
 DowJonesInstrumentType        NO                 NO
 DowJonesInstrumentSubType     NO                 NO
```

**Not queried (6):** VolumeDollarAvg50D, IPODate, DowJonesKey, ChartingSymbol,
DowJonesInstrumentType, DowJonesInstrumentSubType

**Queried but discarded (1):** MarketCapIntraday is in `WATCHLIST_COLUMNS` but
`parse_adhoc_screen_response` never extracts it into `WatchlistEntry`.

---

## Section 3: Parser/Model Gaps (Data We Query But Throw Away)

These fields exist in our `.graphql` queries, the API returns them, and our parsers
silently ignore them. This is the largest category of data loss.

### 3.1 OtherMarketData - Valuation Ratios (HIGH PRIORITY)

Seven valuation metrics are queried in `other_market_data.graphql` (lines 164-193)
under `intradayStatistics` but `parse_stock_response` never extracts them.

```text
 GraphQL Field                  Value from HAR (VRT)   In Model?
 ------------------------------  ---------------------  ---------
 yield                           (dividend yield)       NO
 priceToCashFlowRatio            (price/cash flow)      NO
 forwardPriceToEarningsRatio     (forward P/E)          NO
 priceToSalesRatio               (P/S ratio)            NO
 priceToEarningsRatio            (trailing P/E)         NO
 priceToEarningsVsSP500          (relative P/E)         NO
 cashFlowPerShareLastYear        5.41                   NO
```

**Impact:** No fundamental valuation data available to users despite the API returning
it on every `get_stock()` call. Users needing P/E, P/S, forward P/E, or yield must
use a different data source.

### 3.2 OtherMarketData - Moving Average Distances (HIGH PRIORITY)

The `pricePercentChangeVs` array returns 16 subjects. `PricePercentChanges` only
captures 9, discarding 7 - including all moving average distances.

```text
 Subject             HAR Value (VRT)  Captured?
 -------------------  ---------------  ---------
 VS_YTD               70.46%           YES
 VS_MTD               8.34%            YES
 VS_QTD               70.46%           YES
 VS_WTD               7.93%            YES
 VS_1D_AGO            1.95%            YES
 VS_1M_AGO            5.33%            YES
 VS_3M_AGO            68.04%           YES
 VS_YEAR_HIGH         -0.22%           YES
 VS_YEAR_LOW          0.00%            YES
 VS_5D_AGO            N/A              NO
 VS_SP500_26W_AGO     23.13%           NO
 VS_MA10D             4.51%            NO
 VS_MA21D             6.39%            NO
 VS_MA50D             22.67%           NO
 VS_MA150D            51.17%           NO
 VS_MA200D            63.37%           NO
```

**Impact:** Users cannot determine how far a stock is extended above key moving
averages, a core requirement for Minervini's Trend Template and CANSLIM methodology.
The % distance above the 50-day and 200-day MAs are among the most frequently
checked metrics in growth stock analysis.

### 3.3 OtherMarketData - Alpha/Beta (HIGH PRIORITY)

Both CAPM metrics are queried (`other_market_data.graphql` lines 110-118) and
returned by the API, but `parse_stock_response` never reads them.

```text
 GraphQL Field   HAR Response Shape            In Model?
 --------------  ----------------------------  ---------
 alpha           { value, scalingFactor,        NO
                   formattedValue }
 beta            { value, scalingFactor,        NO
                   formattedValue }
```

### 3.4 OtherMarketData - Short Interest Details (HIGH PRIORITY)

The `shortInterest` object has four sub-fields. Only `percentOfFloat` is captured.

```text
 Field                       HAR Value (VRT)  Captured?
 --------------------------  ---------------  ---------
 percentOfFloat              2.40             YES (Pricing.short_interest_percent_float)
 daysToCover                 1.40             NO
 daysToCoverPercentChange    30.60            NO
 volume                      8,912,395        NO
```

**Impact:** Short squeeze analysis requires days-to-cover and short volume, not
just percent of float.

### 3.5 OtherMarketData - Industry Group History (MEDIUM PRIORITY)

The `industry.groupRanks` and `industry.groupRS` arrays each return 6 time
snapshots. Only the first (CURRENT) is extracted.

```text
 groupRanks snapshots:
 periodOffset   Value (VRT)  Captured?
 -------------  -----------  ---------
 CURRENT        13           YES (Company.industry_group_rank)
 P1W_AGO        20           NO
 P4W_AGO        12           NO
 P12W_AGO       41           NO
 P26W_AGO       26           NO
 P52W_AGO       26           NO

 groupRS snapshots:
 periodOffset   Value  Letter  Captured?
 -------------  -----  ------  ---------
 CURRENT        93     A+      YES (Company.industry_group_rs, industry_group_rs_letter)
 P1W_AGO        90     n/a     NO
 P4W_AGO        94     n/a     NO
 P12W_AGO       78     n/a     NO
 P26W_AGO       87     n/a     NO
 P52W_AGO       87     n/a     NO
```

**Impact:** Users cannot see whether an industry group is improving or deteriorating
in rank over time, a key factor in sector rotation analysis.

### 3.6 OtherMarketData - Historical Price Statistics (MEDIUM PRIORITY)

The `historicalPriceStatistics` object returns quarterly high/low/close with dates.
Completely ignored by the parser.

```text
 Field                 Description                In Model?
 --------------------  -------------------------  ---------
 period                Time period (P1Q)          NO
 periodOffset          Offset from current        NO
 periodEndDate         End of period              NO
 priceHighDate         Date of high               NO
 priceHigh             High price                 NO
 priceLowDate          Date of low                NO
 priceLow              Low price                  NO
 priceClose            Close price                NO
 pricePercentChange    Period return               NO
```

### 3.7 OtherMarketData - Volume Moving Averages (MEDIUM PRIORITY)

`volumeMovingAverages` returns volume MAs with period/offset data. Ignored entirely.

```text
 Field         Description               In Model?
 ------------  ------------------------  ---------
 value         Moving average volume     NO
 period        MA period                 NO
 periodOffset  Time offset               NO
```

### 3.8 OtherMarketData - Blue Dot Boolean Flags (LOW PRIORITY)

Two boolean convenience fields indicate whether today qualifies as a blue dot event.
The dates are captured, but the quick-check booleans are not.

```text
 Field                  HAR Value (VRT)  Captured?
 ---------------------  ---------------  ---------
 isDailyBlueDotEvent    false            NO
 isWeeklyBlueDotEvent   false            NO
```

### 3.9 OtherMarketData - Pricing Date Range (LOW PRIORITY)

```text
 Field             Description                    In Model?
 ----------------  -----------------------------  ---------
 pricingStartDate  Earliest available price data   NO
 pricingEndDate    Latest available price data     NO
```

### 3.10 OtherMarketData - Instrument SubType (LOW PRIORITY)

`symbology.instrument.subType` is queried but not extracted. Distinguishes common
stock from ETF, ADR, etc.

### 3.11 OtherMarketData - Quarterly Data Period Field (LOW PRIORITY)

The `reportedEarnings` and `reportedSales` both include a `period` field (e.g. `P1Q`
for quarterly, `P1Y` for annual) that is queried but not stored in
`QuarterlyReportedPeriod`. Users cannot distinguish quarterly from annual results
without this.

### 3.12 OtherMarketData - Volume % Change Subjects (LOW PRIORITY)

`volumePercentChangeVs` returns multiple subjects, but only `VS_MA50D` is extracted
into `Pricing.volume_percent_change_vs_50d`. Other subjects (e.g. VS_1D_AGO) are
discarded.

### 3.13 ChartMarketData - Quote Formatted Values (LOW PRIORITY)

The chart query requests `formattedValue` alongside `value` for quote fields
(last, volume, percentChange, netChange). The `Quote` model only stores the raw
numeric `value`, discarding formatted strings. This is minor since raw values can
be formatted client-side.

---

## Section 4: Priority Ranking

### Tier 1 - High Value, Low Effort (add fields to existing models + parsers)

These are fields already returned by the API on every `get_stock()` call. Only the
parser and model need updating.

| # | Gap | Fields | Why It Matters |
|---|-----|--------|----------------|
| 1 | Moving average distances | VS_MA10D, VS_MA21D, VS_MA50D, VS_MA150D, VS_MA200D | Core of Minervini Trend Template. "Is the stock above the 50-day?" is the most basic growth stock check. |
| 2 | Valuation ratios | P/E, forward P/E, P/S, P/CF, yield, P/E vs S&P500 | Every fundamental screener needs these. Currently zero valuation data in the library. |
| 3 | Cash flow per share | cashFlowPerShareLastYear | CAN SLIM "C" factor, one field to add. |
| 4 | Alpha/beta | alpha, beta | Risk-adjusted return metrics, two fields to add. |
| 5 | Short interest detail | daysToCover, daysToCoverPercentChange, shortVolume | Short squeeze screening requires more than just % of float. |
| 6 | Industry group history | 5 historical snapshots each for groupRanks and groupRS | Sector rotation timing. Is the group accelerating or fading? |
| 7 | Blue dot booleans | isDailyBlueDotEvent, isWeeklyBlueDotEvent | Convenience flags, trivial to add. |
| 8 | VS_SP500_26W_AGO, VS_5D_AGO | Two more price change subjects | Relative strength vs benchmark, 5-day momentum. |

### Tier 2 - Medium Value, Low Effort (add to query + model + parser)

| # | Gap | Fields | Why It Matters |
|---|-----|--------|----------------|
| 9 | Company location | city, country, stateProvince | Geographic filtering, three fields to add to query + model. |
| 10 | Instrument subType | subType (already queried) | Distinguish common stock from ETF/ADR, parser-only fix. |
| 11 | Quarterly period type | period field in reportedEarnings/Sales | Distinguish quarterly vs annual results, model-only fix. |
| 12 | Watchlist MarketCapIntraday | Already queried | Parser extracts it but WatchlistEntry doesn't have the field. |

### Tier 3 - Medium Value, More Effort (new model structures)

| # | Gap | Fields | Why It Matters |
|---|-----|--------|----------------|
| 13 | Historical price stats | Full quarterly price history | Useful but requires a new model class for the nested structure. |
| 14 | Volume moving averages | volumeMovingAverages array | Requires new list-based field on Pricing model. |
| 15 | Adhoc screen extra columns | IPODate, DowJonesKey, ChartingSymbol, VolumeDollarAvg50D, InstrumentType/SubType | Requires expanding WATCHLIST_COLUMNS and WatchlistEntry. |

### Tier 4 - Low Value (nice-to-have)

| # | Gap | Fields | Why It Matters |
|---|-----|--------|----------------|
| 16 | Pricing date range | pricingStartDate, pricingEndDate | Edge case: know how far back data goes. |
| 17 | Quote formatted values | formattedValue on quote fields | Convenience only, raw values suffice. |
| 18 | Volume change subjects | Additional volumePercentChangeVs subjects | Less commonly used than price subjects. |

---

## Section 5: Detailed Field Inventory

### 5.1 What `parse_stock_response` Extracts Today

For reference, here is every field currently extracted from OtherMarketData:

**Ratings (5 fields):**
composite, eps, rs, smr (letter), ad (letter)

**Company (14 fields):**
name, industry, sector, industry_group_rank (current only), industry_group_rs
(current only), industry_group_rs_letter, description, website, address, address2,
phone, ipo_date, ipo_price, ipo_price_formatted

**Pricing (14 fields):**
market_cap, market_cap_formatted, avg_dollar_volume_50d, avg_dollar_volume_50d_formatted,
up_down_volume_ratio, up_down_volume_ratio_formatted, atr_percent_21d,
atr_percent_21d_formatted, short_interest_percent_float,
short_interest_percent_float_formatted, blue_dot_daily_dates, blue_dot_weekly_dates,
ant_dates, volume_percent_change_vs_50d

**PricePercentChanges (9 fields):**
ytd, mtd, qtd, wtd, vs_1d, vs_1m, vs_3m, vs_year_high, vs_year_low

**Financials (10 fields):**
eps_due_date, eps_due_date_status, eps_last_reported_date, eps_growth_rate,
sales_growth_rate_3y, pre_tax_margin, after_tax_margin, gross_margin,
return_on_equity, earnings_stability

**CorporateActions (4 fields):**
next_ex_dividend_date, dividends list, splits list, spinoffs list

**Industry (4 fields):**
name, sector, code, number_of_stocks

**BasicOwnership (2 fields):**
funds_float_pct, funds_float_pct_formatted

**Fundamentals (4 fields):**
r_and_d_percent_last_qtr, r_and_d_percent_last_qtr_formatted, debt_percent_formatted,
new_ceo_date

**QuarterlyFinancials (5 lists):**
reported_earnings, reported_sales, eps_estimates, sales_estimates, profit_margins

**Patterns:** All 9 pattern types fully parsed.
**TightAreas:** Fully parsed.

### 5.2 What `parse_stock_response` Discards

Every field below is present in the API response but never reaches a model:

```text
 VALUATION & INCOME
   yield { value, scalingFactor, formattedValue }
   priceToCashFlowRatio { value, scalingFactor, formattedValue }
   forwardPriceToEarningsRatio { value, scalingFactor, formattedValue }
   priceToSalesRatio { value, scalingFactor, formattedValue }
   priceToEarningsRatio { value, scalingFactor, formattedValue }
   priceToEarningsVsSP500 { value, scalingFactor, formattedValue }
   cashFlowPerShareLastYear { value, formattedValue }

 MOVING AVERAGE DISTANCES (from pricePercentChangeVs)
   VS_MA10D    (% above/below 10-day MA)
   VS_MA21D    (% above/below 21-day MA)
   VS_MA50D    (% above/below 50-day MA)
   VS_MA150D   (% above/below 150-day MA)
   VS_MA200D   (% above/below 200-day MA)
   VS_5D_AGO   (5-day price change)
   VS_SP500_26W_AGO  (performance vs S&P 500 over 26 weeks)

 RISK METRICS
   alpha { value, scalingFactor, formattedValue }
   beta { value, scalingFactor, formattedValue }

 SHORT INTEREST (3 of 4 sub-fields)
   shortInterest.daysToCover { value, formattedValue }
   shortInterest.daysToCoverPercentChange { value, formattedValue }
   shortInterest.volume { value, scalingFactor, formattedValue }

 INDUSTRY GROUP HISTORY (5 historical snapshots per array)
   groupRanks[1..5] (P1W_AGO through P52W_AGO)
   groupRS[1..5] (P1W_AGO through P52W_AGO)

 BLUE DOT FLAGS
   isDailyBlueDotEvent (boolean)
   isWeeklyBlueDotEvent (boolean)

 HISTORICAL PRICES (entire object ignored)
   historicalPriceStatistics { period, periodOffset, periodEndDate,
     priceHighDate, priceHigh, priceLowDate, priceLow,
     priceClose, pricePercentChange }

 VOLUME
   volumeMovingAverages[] { value, period, periodOffset }
   pricingStartDate { value }
   pricingEndDate { value }

 INSTRUMENT
   symbology.instrument.subType

 QUARTERLY DATA
   reportedEarnings[].period (distinguishes P1Q from P1Y)
```

---

## Section 6: ChartMarketData, Fundamentals, Ownership (Minimal Gaps)

### ChartMarketData

The codebase `.graphql` and parser are well aligned with the HAR. All key fields
(timeSeries, quote, premarketQuote, postmarketQuote, currentMarketState, exchangeData
with holidays) are queried and parsed. The only minor gap is that `formattedValue`
strings on quote fields (last, volume, percentChange, netChange) are discarded in
favor of raw numeric values. This is acceptable.

### FundermentalDataBox

The codebase query matches the HAR query field-for-field. The parser extracts all
requested data into `FundamentalData`. No gaps.

### Ownership

The codebase query matches the HAR query. The parser extracts `fundsFloatPercentHeld`
and `fundOwnershipSummary` (quarterly fund counts). No gaps.

---

## Section 7: Recommendations

### Quick Wins (parser + model changes only, no query changes needed)

1. Add ~15 fields to `Pricing` model for valuation ratios, alpha/beta, short
   interest details, blue dot booleans
2. Add 7 fields to `PricePercentChanges` for MA distances and additional subjects
3. Add `cash_flow_per_share` to `Financials`
4. Restructure `Industry` to hold historical group rank/RS arrays instead of
   flattening to current-only
5. Add `period` to `QuarterlyReportedPeriod`
6. Extract `subType` from instrument into `Company` model
7. Add `market_cap` to `WatchlistEntry` (already queried)

### Small Query Changes

8. Add `city`, `country`, `stateProvince` to `symbology.company` in
   `other_market_data.graphql`
9. Add IPODate, DowJonesKey, ChartingSymbol, VolumeDollarAvg50D to
   `WATCHLIST_COLUMNS` in `_queries.py`
