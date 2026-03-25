# tickerscope

[![CI](https://github.com/major/tickerscope/actions/workflows/ci.yml/badge.svg)](https://github.com/major/tickerscope/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tickerscope)](https://pypi.org/project/tickerscope/)
[![Python](https://img.shields.io/pypi/pyversions/tickerscope)](https://pypi.org/project/tickerscope/)
[![License](https://img.shields.io/pypi/l/tickerscope)](https://github.com/major/tickerscope/blob/main/LICENSE)

Unofficial async Python client for the [MarketSurge](https://marketsurge.investors.com/) stock research API.
Wraps the GraphQL endpoints with typed dataclass models and cookie-based auth.

> [!IMPORTANT]
> This is an **unofficial** library. You need an active MarketSurge subscription and must be logged in via your browser for authentication to work.

## Features

- Sync and async clients (`TickerScopeClient` / `AsyncTickerScopeClient`)
- Frozen dataclass models with JSON serialization
- Automatic JWT auth from browser cookies (Firefox/Chrome) via [rookiepy](https://github.com/thewh1teagle/rookiepy)
- Token expiry detection and structured error hierarchy

## Installation

```bash
pip install tickerscope
```

## Authentication

tickerscope authenticates by extracting cookies from your browser. Log into
[MarketSurge](https://marketsurge.investors.com/) in Firefox or Chrome first, then:

```python
from tickerscope import TickerScopeClient

# Reads cookies from Firefox by default
client = TickerScopeClient()

# Or specify Chrome
client = TickerScopeClient(browser="chrome")
```

You can also pass a JWT directly or set the `TICKERSCOPE_JWT` environment variable:

```python
client = TickerScopeClient(jwt="your-jwt-token")
```

## Usage

### Sync client

```python
from tickerscope import TickerScopeClient

with TickerScopeClient() as client:
    stock = client.get_stock("AAPL")
    print(stock.ratings.composite)
    print(stock.pricing.price)

    chart = client.get_chart_data(
        "AAPL",
        start_date="2025-01-01",
        end_date="2025-03-01",
    )
    for point in chart.time_series.data_points[:5]:
        print(point.close, point.volume)
```

### Async client

```python
import asyncio
from tickerscope import AsyncTickerScopeClient

async def main():
    async with AsyncTickerScopeClient() as client:
        stock = await client.get_stock("NVDA")
        print(stock.company.name, stock.ratings.composite)

        fundamentals = await client.get_fundamentals("NVDA")
        for period in fundamentals.reported_earnings:
            print(period.period_label, period.value)

asyncio.run(main())
```

### Async client (fully async construction)

Use the `create()` factory for fully async initialization, including the auth
HTTP request:

```python
async def main():
    client = await AsyncTickerScopeClient.create()
    try:
        stock = await client.get_stock("TSLA")
        print(stock.ratings)
    finally:
        await client.aclose()
```

## Available methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_stock(symbol)` | `StockData` | Ratings, pricing, financials, patterns |
| `get_chart_data(symbol, ...)` | `ChartData` | OHLCV time series and quotes |
| `get_fundamentals(symbol)` | `FundamentalData` | Earnings/sales reported and estimates |
| `get_ownership(symbol)` | `OwnershipData` | Institutional fund ownership |
| `get_watchlist(list_id)` | `list[WatchlistEntry]` | Screen a watchlist for stock data |
| `get_watchlist_names()` | `list[WatchlistSummary]` | All user watchlists |
| `get_watchlist_symbols(id)` | `WatchlistDetail` | Symbol keys in a watchlist |
| `get_watchlist_by_name(name)` | `WatchlistDetail` | Look up watchlist by name |
| `get_screens()` | `list[Screen]` | Saved stock screens |
| `get_screen_by_name(name)` | `Screen` | Look up screen by name |
| `run_screen(name, params)` | `ScreenResult` | Execute a stock screen |
| `get_active_alerts()` | `AlertSubscriptionList` | Active alert subscriptions |
| `get_triggered_alerts()` | `TriggeredAlertList` | Recently triggered alerts |
| `get_layouts()` | `list[Layout]` | Saved chart layouts |
| `get_chart_markups(symbol)` | `ChartMarkupList` | Chart annotations/markups |

## Error handling

All exceptions inherit from `TickerScopeError` and include a `to_dict()` method
for structured error reporting:

```python
from tickerscope import (
    TickerScopeError,
    AuthenticationError,
    CookieExtractionError,
    TokenExpiredError,
    APIError,
    SymbolNotFoundError,
)

try:
    stock = client.get_stock("INVALID")
except SymbolNotFoundError as exc:
    print(exc.symbol)
    print(exc.to_dict())
except TokenExpiredError:
    # Re-authenticate and retry
    ...
```

## Development

Requires [uv](https://docs.astral.sh/uv/) for dependency management:

```bash
uv sync --all-extras --dev

make lint        # ruff check
make typecheck   # ty check
make radon       # cyclomatic complexity gate (A/B only)
make test        # pytest with coverage
make ci          # all of the above
```

## License

MIT
