# Getting Started

## Prerequisites

1. An active [MarketSurge](https://marketsurge.investors.com/) subscription
2. Logged into MarketSurge in **Firefox** or **Chrome**
3. Python 3.10+

## Installation

```bash
pip install tickerscope
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add tickerscope
```

## Authentication

tickerscope authenticates by extracting cookies from your browser and exchanging them for a JWT token. There are three ways to provide credentials, checked in this order:

### 1. Direct JWT parameter

Pass a token directly when creating the client:

```python
client = TickerScopeClient(jwt="your-jwt-token")
```

### 2. Environment variable

Set the `TICKERSCOPE_JWT` environment variable:

```bash
export TICKERSCOPE_JWT="your-jwt-token"
```

```python
# Picks up the token automatically
client = TickerScopeClient()
```

### 3. Browser cookie extraction (default)

If no JWT is provided, tickerscope extracts cookies from your browser using [rookiepy](https://github.com/thewh1teagle/rookiepy) and exchanges them for a token:

```python
# Firefox (default)
client = TickerScopeClient()

# Chrome
client = TickerScopeClient(browser="chrome")
```

!!! tip

    Browser cookie extraction requires that you're actively logged into MarketSurge.
    If you see `CookieExtractionError`, open MarketSurge in your browser and log in first.

## Your first API call

### Sync client

The sync client uses a standard context manager:

```python
from tickerscope import TickerScopeClient

with TickerScopeClient() as client:
    stock = client.get_stock("AAPL")
    print(stock.company.name)       # Apple Inc.
    print(stock.ratings.composite)  # 85
    print(stock.ratings.rs)         # 72
```

Without a context manager, call `close()` when done:

```python
client = TickerScopeClient()
try:
    stock = client.get_stock("AAPL")
finally:
    client.close()
```

### Async client

The async client supports `async with`:

```python
import asyncio
from tickerscope import AsyncTickerScopeClient

async def main():
    async with AsyncTickerScopeClient() as client:
        stock = await client.get_stock("NVDA")
        print(stock.company.name)
        print(stock.ratings.composite)

asyncio.run(main())
```

Without a context manager, call `aclose()`:

```python
client = AsyncTickerScopeClient()
try:
    stock = await client.get_stock("NVDA")
finally:
    await client.aclose()
```

### Fully async construction

The standard `AsyncTickerScopeClient()` constructor performs JWT resolution synchronously (cookie extraction reads local files). If you need fully async initialization, including the HTTP auth request, use the `create()` factory:

```python
async def main():
    client = await AsyncTickerScopeClient.create()
    try:
        stock = await client.get_stock("TSLA")
        print(stock.ratings)
    finally:
        await client.aclose()
```

## Checking token expiry

JWT tokens expire after a period. You can check before making calls:

```python
from tickerscope import is_token_expired

if client.is_token_expired:
    # Re-create the client to get a fresh token
    client = TickerScopeClient()
```

Or check a raw token string:

```python
from tickerscope import is_token_expired

expired = is_token_expired("eyJhbGciOi...")
```

## Client options

Both clients accept the same constructor parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `browser` | `str` | `"firefox"` | Browser for cookie extraction (`"firefox"` or `"chrome"`) |
| `timeout` | `float` | `30.0` | HTTP request timeout in seconds |
| `jwt` | `str \| None` | `None` | Direct JWT token (keyword-only, skips browser auth) |
