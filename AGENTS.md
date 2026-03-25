# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-23
**Commit:** f2453ae
**Branch:** main

## OVERVIEW

Unofficial async Python client library (`tickerscope`) for the MarketSurge stock research API. Wraps GraphQL endpoints with typed dataclass models, cookie-based auth, and optional caching via aiocache.

## STRUCTURE

```text
marketsurge/
  src/tickerscope/        # Library package (private modules, _ prefix)
    queries/              # .graphql files loaded via importlib.resources
  tests/                  # pytest suite with JSON fixtures
    fixtures/             # API response fixtures (12 JSON files)
  Makefile                # lint, format, typecheck, radon, test, ci
  pyproject.toml          # uv_build backend, deps, pytest config
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add API endpoint | `_client.py` + `_parsing.py` + `queries/` | Build payload, add parser, add .graphql |
| Add data model | `_models.py` + `__init__.py` | Frozen dataclass + SerializableDataclass, export in `__all__` |
| Auth/JWT flow | `_auth.py` | resolve_jwt chain: param -> env -> cookie -> exchange |
| Date handling | `_dates.py` | Always timezone-aware, never naive datetimes |
| Caching | `_cache.py` | MethodCache wraps aiocache (optional dep) |
| Exceptions | `_exceptions.py` | Hierarchy: TickerScopeError base, all have `to_dict()` |
| GraphQL queries | `queries/*.graphql` + `_queries.py` | Loaded via `load_query()`, constants in `_queries.py` |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| BaseTickerScopeClient | Class | _client.py:73 | ABC with all `_build_*_payload` + `_graphql_and_parse` |
| TickerScopeClient | Class | _client.py:613 | Sync client, context manager |
| AsyncTickerScopeClient | Class | _client.py:697 | Async client, factory via `create()`, caching support |
| StockData | Class | _models.py:360 | Top-level stock model (ratings, pricing, financials, patterns) |
| ChartData | Class | _models.py:826 | OHLCV time series + quotes |
| FundamentalData | Class | _models.py:927 | Earnings/sales reported + estimates |
| AlertSubscriptionList | Class | _models.py:1060 | Active alert subscriptions |
| resolve_jwt / async_resolve_jwt | Func | _auth.py:83/136 | JWT resolution chain |
| authenticate / async_authenticate | Func | _auth.py:22/163 | Cookie extraction + JWT exchange |
| parse_stock_response | Func | _parsing.py:99 | Largest parser (~200 lines), extracts StockData |
| MethodCache | Class | _cache.py:8 | Optional aiocache wrapper with TTL |
| SerializableDataclass | Class | _serialization.py:15 | Base class for dict/JSON serialization (to_dict, from_dict, to_json) |

## CONVENTIONS

- **`from __future__ import annotations`** in every module
- **Private modules**: underscore prefix (`_client.py`, not `client.py`)
- **Models**: frozen dataclasses with `SerializableDataclass`
  - Date string fields get `_dt` property counterparts (e.g., `ipo_date` -> `ipo_date_dt`)
- **Logger**: module-level `_log = logging.getLogger("tickerscope")`
- **Type checker**: `ty` (in Makefile), pyright inline ignores in code (`# pyright: ignore[...]`)
- **`# noqa: F401`**: on imports kept solely for test patching

## ANTI-PATTERNS (THIS PROJECT)

- **Never parse opaque fields**: `TriggeredAlert.payload` (dict) and `ChartMarkup.data` (str) are pass-through
- **Never return naive datetimes**: `_dates.py` guarantees `tzinfo` is always set
- **Never suppress type errors**: no `as any` / `@ts-ignore` equivalents
- **Radon gate**: cyclomatic complexity C or higher fails the build (`make radon`)

## COMMANDS

```bash
uv sync                  # Install deps
make test                # pytest -v --cov
make lint                # ruff check src/ tests/
make format              # ruff format src/ tests/
make typecheck           # ty check src/
make radon               # Fail on complexity >= C
make ci                  # lint + typecheck + radon + test
```

## NOTES

- **Repo vs package name**: repo is `marketsurge`, package is `tickerscope`
- **Makefile test target** references `--cov=okp_mcp` (likely stale, should be `--cov=tickerscope`)
- **Empty README.md**: no documentation yet
- **No CI/CD**: no GitHub Actions or similar
- **TICKERSCOPE_JWT** env var: direct JWT bypass, skips cookie extraction
- **rookiepy**: extracts browser cookies (Firefox/Chrome) for auth - fragile, breaks on browser updates
- **aiocache** is optional (`pip install tickerscope[cache]`), MethodCache gracefully degrades
