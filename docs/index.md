# tickerscope

Unofficial async Python client for the [MarketSurge](https://marketsurge.investors.com/) stock research API. Wraps GraphQL endpoints with typed dataclass models, cookie-based auth, and optional caching.

!!! warning "Unofficial"

    This is an **unofficial** library. You need an active MarketSurge subscription
    and must be logged in via your browser for authentication to work.

## Features

- **Sync and async clients** with context manager support
- **Frozen dataclass models** with full JSON serialization (`to_dict`, `to_json`, `from_dict`)
- **Automatic JWT auth** from browser cookies (Firefox/Chrome) via [rookiepy](https://github.com/thewh1teagle/rookiepy)
- **Token expiry detection** with `is_token_expired` helper
- **Structured error hierarchy** with `to_dict()` on every exception
- **Rich stock data** including ratings, pricing, financials, chart patterns, and ownership
- **Watchlist and screen management** with discovery, lookup, and execution
- **Predefined reports** covering breakouts, bases forming, earnings gaps, and more

## Quick example

=== "Async"

    ```python
    import asyncio
    from tickerscope import AsyncTickerScopeClient

    async def main():
        async with AsyncTickerScopeClient() as client:
            stock = await client.get_stock("NVDA")
            print(stock.company.name, stock.ratings.composite)

    asyncio.run(main())
    ```

=== "Sync"

    ```python
    from tickerscope import TickerScopeClient

    with TickerScopeClient() as client:
        stock = client.get_stock("AAPL")
        print(stock.company.name, stock.ratings.composite)
    ```

## Installation

```bash
pip install tickerscope
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add tickerscope
```

## What's next?

| Guide | Description |
|-------|-------------|
| [Getting Started](getting-started.md) | Authentication setup, your first API call |
| [Stock Data](stock-data.md) | Fetch ratings, charts, fundamentals, ownership |
| [Watchlists & Screens](watchlists-and-screens.md) | Discover and run watchlists, screens, and reports |
| [Error Handling](error-handling.md) | Exception hierarchy and recovery patterns |
| [Serialization](serialization.md) | Export data as dicts/JSON, date properties |
| [API Reference](reference/) | Auto-generated docs for all classes and methods |
