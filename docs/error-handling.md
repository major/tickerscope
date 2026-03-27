# Error Handling

All tickerscope exceptions inherit from [`TickerScopeError`][tickerscope.TickerScopeError] and include a `to_dict()` method for structured error reporting.

## Exception hierarchy

```text
TickerScopeError            Base exception for all library errors
  AuthenticationError       JWT exchange failed or user not logged in
    CookieExtractionError   Browser cookie extraction failed
    TokenExpiredError       JWT expired or rejected (HTTP 401)
  APIError                  GraphQL API returned errors
    SymbolNotFoundError     Requested symbol not found
  HTTPError                 Non-auth HTTP errors (429, 5xx, etc.)
```

## Common patterns

### Catching all tickerscope errors

```python
from tickerscope import TickerScopeError

try:
    stock = client.get_stock("AAPL")
except TickerScopeError as exc:
    print(exc.user_message)  # Human-friendly message
    print(exc.to_dict())     # Structured dict for logging
```

### Handling symbol not found

```python
from tickerscope import SymbolNotFoundError

try:
    stock = client.get_stock("XYZZY")
except SymbolNotFoundError as exc:
    print(exc.symbol)        # "XYZZY"
    print(exc.user_message)  # "Symbol 'XYZZY' not found. Check the ticker spelling."
```

### Handling expired tokens

```python
from tickerscope import TickerScopeClient, TokenExpiredError

client = TickerScopeClient()

try:
    stock = client.get_stock("AAPL")
except TokenExpiredError:
    # Re-create client to get a fresh token
    client.close()
    client = TickerScopeClient()
    stock = client.get_stock("AAPL")
```

You can also check proactively before making calls:

```python
if client.is_token_expired:
    client.close()
    client = TickerScopeClient()
```

### Handling auth failures

```python
from tickerscope import AuthenticationError, CookieExtractionError

try:
    client = TickerScopeClient()
except CookieExtractionError as exc:
    print(exc.browser)       # "firefox"
    print(exc.user_message)  # "Could not extract cookies from firefox. ..."
except AuthenticationError as exc:
    print(exc.user_message)  # "Authentication failed. ..."
```

### Handling HTTP errors

Non-auth HTTP errors (rate limiting, server errors) raise [`HTTPError`][tickerscope.HTTPError]:

```python
from tickerscope import HTTPError

try:
    stock = client.get_stock("AAPL")
except HTTPError as exc:
    print(exc.status_code)    # 429, 500, etc.
    print(exc.message)        # "Rate limited, retry after a delay"
    print(exc.response_body)  # Raw response text
```

### Handling API-level errors

GraphQL can return errors even on HTTP 200. These raise [`APIError`][tickerscope.APIError]:

```python
from tickerscope import APIError

try:
    entries = client.get_watchlist(watchlist_id=99999)
except APIError as exc:
    print(exc.errors)  # List of GraphQL error dicts
```

## Structured error reporting with `to_dict()`

Every exception provides a `to_dict()` method that returns a JSON-serializable dict, useful for structured logging:

```python
import json
import logging

logger = logging.getLogger(__name__)

try:
    stock = client.get_stock("XYZZY")
except TickerScopeError as exc:
    logger.error("API call failed: %s", json.dumps(exc.to_dict()))
```

Each exception type includes different fields:

```python
# SymbolNotFoundError
{
    "error_type": "symbol_not_found",
    "message": "No market data returned for symbol 'XYZZY'",
    "user_message": "Symbol 'XYZZY' not found. Check the ticker spelling.",
    "symbol": "XYZZY"
}

# TokenExpiredError
{
    "error_type": "token_expired",
    "message": "JWT token has expired or is invalid (HTTP 401)",
    "user_message": "Authentication token expired. Re-authenticate to continue.",
    "status_code": 401
}

# HTTPError
{
    "error_type": "http_error",
    "status_code": 429,
    "message": "Rate limited, retry after a delay",
    "response_body": "...",
    "user_message": "MarketSurge returned an HTTP 429 error."
}
```

## User-friendly messages

Every exception has a `user_message` property that returns a plain-English explanation suitable for showing to end users:

```python
try:
    stock = client.get_stock("AAPL")
except TickerScopeError as exc:
    # Show to user
    print(exc.user_message)
    # Log details for debugging
    logger.debug("Details: %s", exc.to_dict())
```
