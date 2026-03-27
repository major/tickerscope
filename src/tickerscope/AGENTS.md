# tickerscope Package Internals

**Focus**: Module-level architecture and patterns for AI agents working within `src/tickerscope/`.

## OVERVIEW

Private module package (`_*` prefix) wrapping MarketSurge GraphQL API. Frozen dataclass models with SerializableDataclass, async-first client with optional caching, and defensive parsing from opaque JSON responses.

## WHERE TO LOOK

| Task | Module | Key Symbol |
|------|--------|-----------|
| Add API endpoint | `_queries.py` + `queries/*.graphql` | load_query() |
| Add endpoint handler | `_client.py` | BaseTickerScopeClient._build_*_payload |
| Add response parser | `_parsing.py` | parse_*_response functions |
| Add data model | `_models.py` | Frozen dataclass + SerializableDataclass |
| Handle dates | `_dates.py` | parse_datetime (always tz-aware) |
| Auth/JWT flow | `_auth.py` | resolve_jwt chain |
| Caching layer | `_cache.py` | MethodCache (optional aiocache) |
| Error handling | `_exceptions.py` | TickerScopeError hierarchy |
| Pagination/filtering | `_client.py` | _filter_watchlist_entries, _paginate_list |
| Field selection | `_serialization.py` | to_dict(fields=...) |

## MODULE SIZES

| Module | Lines | Complexity notes |
|--------|-------|-----------------|
| _client.py | ~2100 | Three client classes, async overrides, pagination/filtering helpers |
| _models.py | ~1470 | 70+ dataclasses, largest file |
| _parsing.py | ~960 | 13 parsers, helpers: _first, _safe_value, _as_map |
| _auth.py | ~220 | Sync + async variants of resolve/authenticate |
| _serialization.py | ~190 | SerializableDataclass base with field selection |
| _exceptions.py | ~140 | 6-class hierarchy, all with to_dict() |
| _dates.py | ~60 | 3 functions, timezone enforcement |
| _cache.py | ~50 | Single class, optional dep graceful degradation |
| _queries.py | ~40 | Constants + WATCHLIST_COLUMNS definition |

## CONVENTIONS

- **Private modules**: underscore prefix (`_client.py`, not `client.py`)
- **Models**: frozen dataclass + SerializableDataclass (inherits to_dict/to_json/from_dict)
- **Date fields**: string field + `_dt` property (e.g., `ipo_date` -> `ipo_date_dt`)
- **Logger**: `_log = logging.getLogger('tickerscope')` per module
- **Type checking**: pyright inline ignores (`# pyright: ignore[...]`), no `as any` equivalents
- **Pagination**: `run_catalog_entry()`, `run_report()`, `get_watchlist()` accept `limit`, `offset`, `filters`; `CatalogResult.total` holds the pre-pagination count
- **Field selection**: `to_dict(fields={"symbol", "rs_rating"})` filters output recursively

## ENDPOINT WORKFLOW

Adding a new API endpoint:

1. Create `queries/endpoint_name.graphql` with query/mutation
2. Add constant to `_queries.py`: `ENDPOINT_NAME = load_query('endpoint_name')`
3. Add `_build_endpoint_name_payload()` to BaseTickerScopeClient
4. Add `parse_endpoint_name_response()` to _parsing.py
5. Add response model(s) to _models.py
6. Export in `__init__.py` __all__
