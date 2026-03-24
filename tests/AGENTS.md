# Test Suite Knowledge Base

**Generated:** 2026-03-23

## OVERVIEW

25 test files covering client, auth, models, parsing, and API endpoints. Uses respx for HTTP mocking, pytest-randomly for isolation, and asyncio_mode="auto" for async test detection.

## STRUCTURE

```text
tests/
  conftest.py              # 12 shared fixtures loading JSON from fixtures/
  fixtures/                # 12 JSON response files (stock, watchlist, screens, etc.)
  test_client.py           # Sync client tests
  test_async_client.py     # Async client tests
  test_base_client.py      # ABC payload builders
  test_async_factory.py    # create() factory
  test_auth.py             # Cookie extraction + JWT exchange
  test_jwt_auth.py         # JWT validation
  test_token_detection.py  # Token parsing
  test_token_expiry.py     # Expiry handling
  test_models.py           # Frozen dataclass enforcement
  test_serialization.py    # to_dict/to_json + builder helpers
  test_date_properties.py  # _dt property counterparts
  test_str_methods.py      # __str__ implementations
  test_parsing.py          # parse_* functions
  test_caching.py          # Cache hit/miss verification
  test_convenience.py      # get_by_name helpers
  test_capabilities.py     # Feature detection
  test_screens.py          # Screens endpoint
  test_screen_result.py    # Screen result parsing
  test_flagged_symbols.py  # Flagged symbols endpoint
  test_watchlist_names.py  # Watchlist names endpoint
  test_smoke.py            # Fixture validation
  test_public_api.py       # __all__ exports
  test_exceptions.py       # Exception hierarchy
  test_structured_errors.py # Error dict serialization
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add endpoint test | test_<endpoint>.py + conftest.py | Create fixture, add respx route, test payload + parsing |
| Test async code | test_async_*.py | Use async def, yield, await client.aclose() |
| Mock HTTP | @respx.mock + respx.post(...).mock(return_value=...) | Verify route.call_count for caching |
| Mock objects | unittest.mock.patch + spec= | Type-safe mocking with attribute verification |
| Test models | test_models.py + test_serialization.py | Frozen enforcement, to_dict/to_json, builder helpers |
| Test auth | test_auth.py + test_jwt_auth.py | Cookie extraction, JWT exchange, token expiry |
| Bypass auth in fixtures | patch("tickerscope._client.authenticate") or patch("tickerscope._client.resolve_jwt") | Prevents real auth calls in tests |

## CONVENTIONS

- **Fixtures**: Load JSON from fixtures/ via conftest.py, reuse across tests
- **HTTP mocking**: @respx.mock decorator, respx.post(...).mock(return_value=httpx.Response(200, json=fixture))
- **Async fixtures**: async def + yield + await client.aclose() for cleanup
- **Builder helpers**: _minimal_pricing(**overrides), _minimal_stock(**overrides) in test_serialization.py
- **Class-based grouping**: TestAuthenticateSuccess, TestCacheHitSkipsHttp for related tests
- **Docstrings**: Every test has a PEP 257 docstring explaining what it verifies
- **Route counting**: assert route.call_count == 1 to verify caching behavior
- **Frozen validation**: pytest.raises(AttributeError) for immutability checks
- **Signature inspection**: inspect.signature() to verify API contracts
- **Pyright directive**: # pyright: reportMissingImports=false in test files
- **Import preservation**: # noqa: F401 on imports kept solely for test patching paths

## ANTI-PATTERNS

- **Never mock the entire client**: Mock specific methods (authenticate, _graphql_and_parse) not the whole class
- **Never use naive datetimes in fixtures**: All datetime fields must have tzinfo set
- **Never skip async cleanup**: Always await client.aclose() in async fixtures
- **Never hardcode JWT inline**: Define FAKE_JWT as a module-level constant per test file
- **Never test without respx.mock**: Prevents accidental HTTP calls to real API
- **Never ignore route.call_count**: Caching tests must verify routes aren't called twice
- **Never suppress pyright errors**: Use inline directives (# pyright: ignore[...]) not blanket ignores
