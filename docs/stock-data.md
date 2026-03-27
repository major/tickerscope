# Stock Data

tickerscope provides several methods for fetching stock data. All examples use the async client, but the sync client has identical method signatures (just drop `await`).

## Stock profile: `get_stock()`

Returns a [`StockData`][tickerscope.StockData] object with ratings, pricing, financials, company info, chart patterns, and more.

```python
async with AsyncTickerScopeClient() as client:
    stock = await client.get_stock("NVDA")
```

### Ratings

IBD-style composite, EPS, RS, SMR, and accumulation/distribution ratings:

```python
print(stock.ratings.composite)  # 95
print(stock.ratings.eps)        # 99
print(stock.ratings.rs)         # 90
print(stock.ratings.smr)        # "A"
print(stock.ratings.ad)         # "B+"
```

### Company info

```python
print(stock.company.name)                # NVIDIA Corp
print(stock.company.industry)            # Elec-Semiconductor Fabless
print(stock.company.sector)              # Technology
print(stock.company.industry_group_rank) # 3
print(stock.company.ipo_date)            # "1999-01-22"
print(stock.company.ipo_date_dt)         # datetime.date(1999, 1, 22)
```

### Pricing and market data

```python
print(stock.pricing.market_cap_formatted)              # "$3.2T"
print(stock.pricing.avg_dollar_volume_50d_formatted)    # "$42.5B"
print(stock.pricing.up_down_volume_ratio_formatted)     # "1.3"
print(stock.pricing.price_percent_changes.ytd)          # 12.5
print(stock.pricing.price_percent_changes.vs_year_high) # -5.2
```

### Financials

```python
print(stock.financials.eps_growth_rate)       # 122.0
print(stock.financials.sales_growth_rate_3y)  # 69.0
print(stock.financials.pre_tax_margin)        # 64.2
print(stock.financials.eps_due_date)          # "2025-05-28"
print(stock.financials.eps_due_date_dt)       # datetime.date(2025, 5, 28)
```

### Chart patterns

Detected technical patterns (cup with handle, double bottom, flat base, ascending base, IPO base):

```python
for pattern in stock.patterns:
    print(pattern.pattern_type)              # "CUP_WITH_HANDLE"
    print(pattern.base_stage)                # "2"
    print(pattern.pivot_price_formatted)     # "152.89"
    print(pattern.base_depth_formatted)      # "23%"
    print(pattern.base_length)               # 42 (weeks)
    print(pattern.pivot_date_dt)             # datetime.date(2025, 3, 10)
```

Pattern types include [`CupPattern`][tickerscope.CupPattern], [`DoubleBottomPattern`][tickerscope.DoubleBottomPattern], [`AscendingBasePattern`][tickerscope.AscendingBasePattern], and [`IpoBasePattern`][tickerscope.IpoBasePattern], each with additional type-specific fields.

### Quarterly financials

Reported earnings/sales and forward estimates:

```python
qf = stock.quarterly_financials

# Last few quarters of reported EPS
for period in qf.reported_earnings[:4]:
    print(f"Q{period.quarter_number} FY{period.fiscal_year}: "
          f"EPS {period.value}, YoY {period.pct_change_yoy}%")

# Forward EPS estimates
for est in qf.eps_estimates:
    print(f"Est EPS: {est.value}, direction: {est.revision_direction}")
```

## Chart data: `get_chart_data()`

Returns a [`ChartData`][tickerscope.ChartData] object with OHLCV time series, quotes, and exchange info.

### With explicit date range

```python
chart = await client.get_chart_data(
    "AAPL",
    start_date="2025-01-01",
    end_date="2025-03-01",
)
```

### With lookback shorthand

Instead of specifying both dates, use `lookback` to get data relative to today:

```python
chart = await client.get_chart_data("AAPL", lookback="3M")
```

Valid lookback values: `1W`, `1M`, `3M`, `6M`, `1Y`, `YTD`.

!!! warning

    You cannot mix `lookback` with `start_date` or `end_date`. Use one approach or the other.

### Working with time series data

```python
ts = chart.time_series
print(ts.period)  # "P1D" (daily)

for point in ts.data_points[:5]:
    print(f"{point.start_date_time}: "
          f"O={point.open} H={point.high} "
          f"L={point.low} C={point.close} "
          f"V={point.volume}")
```

### Quotes

Current and extended-hours quotes when available:

```python
if chart.quote:
    print(f"Last: {chart.quote.last}")
    print(f"Change: {chart.quote.percent_change}%")
    print(f"Volume: {chart.quote.volume}")

if chart.premarket_quote:
    print(f"Pre-market: {chart.premarket_quote.last}")

if chart.postmarket_quote:
    print(f"After-hours: {chart.postmarket_quote.last}")
```

### Relative strength line

Include a benchmark symbol to get the data needed for an RS line:

```python
chart = await client.get_chart_data(
    "AAPL",
    lookback="1Y",
    benchmark="0S&P5",
)

# benchmark_time_series has the index data
if chart.benchmark_time_series:
    print(f"Benchmark points: {len(chart.benchmark_time_series.data_points)}")
```

### Additional parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `symbol` | `str` | (required) | Ticker symbol |
| `start_date` | `str \| None` | `None` | Start date (`YYYY-MM-DD` format) |
| `end_date` | `str \| None` | `None` | End date (`YYYY-MM-DD` format) |
| `lookback` | `str \| None` | `None` | Relative lookback (`1W`, `1M`, `3M`, `6M`, `1Y`, `YTD`) |
| `period` | `str` | `"P1D"` | Time series period (e.g. `P1D` for daily) |
| `exchange` | `str \| None` | `None` | Exchange name (e.g. `"NYSE"`); omit for a lighter response |
| `benchmark` | `str \| None` | `None` | Benchmark symbol for RS line (e.g. `"0S&P5"`) |

## Fundamentals: `get_fundamentals()`

Returns a [`FundamentalData`][tickerscope.FundamentalData] object with historical earnings/sales and forward estimates on an annual basis.

```python
fundamentals = await client.get_fundamentals("AAPL")
print(fundamentals.company_name)  # "Apple Inc."

# Annual reported earnings
for period in fundamentals.reported_earnings:
    print(f"{period.period_offset}: EPS {period.formatted_value}, "
          f"YoY {period.formatted_pct_change}")

# Annual reported sales
for period in fundamentals.reported_sales:
    print(f"{period.period_offset}: Sales {period.formatted_value}")

# Forward EPS estimates
for est in fundamentals.eps_estimates:
    print(f"Est EPS: {est.formatted_value}, "
          f"revision: {est.revision_direction}")
```

## Ownership: `get_ownership()`

Returns an [`OwnershipData`][tickerscope.OwnershipData] object with institutional fund ownership data.

```python
ownership = await client.get_ownership("AAPL")
print(ownership.funds_float_pct)  # Percentage of float held by funds

for quarter in ownership.quarterly_funds:
    print(f"{quarter.date}: {quarter.count} funds")
```

## Combined analysis: `get_stock_analysis()`

Fetches stock data, fundamentals, and ownership in a single call. Tolerates partial failures: if fundamentals or ownership fails, the other data is still returned.

```python
analysis = await client.get_stock_analysis("AAPL")

# Stock data is always present
print(analysis.stock.ratings.composite)

# Optional sections (may be None if the API call failed)
if analysis.fundamentals:
    print(analysis.fundamentals.reported_earnings[0].formatted_value)

if analysis.ownership:
    print(analysis.ownership.funds_float_pct)

# Any errors from optional sections
for error in analysis.errors:
    print(f"Warning: {error}")
```

The async client fetches all three endpoints concurrently with `asyncio.gather` for better performance.

## RS rating history: `get_rs_rating_history()`

Returns the historical RS rating values for a symbol:

```python
rs_history = await client.get_rs_rating_history("AAPL")
print(rs_history.rs_line_new_high)  # True/False

for snapshot in rs_history.ratings:
    print(f"{snapshot.period_offset}: RS {snapshot.value} ({snapshot.letter_value})")
```
