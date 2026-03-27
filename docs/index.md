# tickerscope

Unofficial async Python client for the [MarketSurge](https://marketsurge.investors.com/) stock research API. Wraps GraphQL endpoints with typed dataclass models, cookie-based auth, and optional caching.

!!! warning "Unofficial"

    This is an **unofficial** library. You need an active MarketSurge subscription
    and must be logged in via your browser for authentication to work.

## Quick example

```python
import asyncio
from tickerscope import AsyncTickerScopeClient

async def main():
    async with AsyncTickerScopeClient() as client:
        stock = await client.get_stock("NVDA")
        print(stock.company.name, stock.ratings.composite)

asyncio.run(main())
```

## Installation

```bash
pip install tickerscope
```

See the **API Reference** section in the navigation for full documentation of all clients, models, and exceptions.
