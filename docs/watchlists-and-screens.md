# Watchlists & Screens

tickerscope provides tools for discovering and running watchlists, stock screens, predefined reports, and coach account screens. All examples use the async client, but the sync client has identical method signatures.

## Watchlists

### List all watchlists

```python
async with AsyncTickerScopeClient() as client:
    watchlists = await client.get_watchlist_names()
    for wl in watchlists:
        print(f"{wl.name} (ID: {wl.id}, modified: {wl.last_modified})")
```

### Look up a watchlist by name

```python
detail = await client.get_watchlist_by_name("My Leaders")
print(f"{detail.name}: {len(detail.items)} symbols")

for item in detail.items:
    print(f"  {item.key}")
```

### Get screened watchlist data

`get_watchlist()` returns full stock data for each symbol in the watchlist, including ratings, price, and industry info:

```python
entries = await client.get_watchlist(watchlist_id=12345)
for entry in entries:
    print(f"{entry.symbol} - {entry.company_name}")
    print(f"  Comp: {entry.composite_rating}, "
          f"EPS: {entry.eps_rating}, "
          f"RS: {entry.rs_rating}")
    print(f"  Price: ${entry.price} ({entry.price_pct_change:+.1f}%)")
```

### Screen a watchlist by name

Combines `get_watchlist_names()` and `get_watchlist()` into one call:

```python
entries = await client.screen_watchlist_by_name("My Leaders")
for entry in entries:
    print(f"{entry.symbol}: RS {entry.rs_rating}")
```

## Stock screens

### List saved screens

```python
screens = await client.get_screens()
for screen in screens:
    print(f"{screen.name} (type: {screen.type})")
```

### Look up a screen by name

```python
screen = await client.get_screen_by_name("High RS Growth")
print(screen.description)
print(screen.filter_criteria)
```

### Run a screen

`run_screen()` requires the fully-qualified predefined screen name and a list of parameter dicts:

```python
result = await client.run_screen(
    screen_name="marketsurge.theme.screen1",
    parameters=[
        {"name": "MinCompositeRating", "value": "90"},
        {"name": "MinEPSRating", "value": "80"},
    ],
)

print(f"Found {result.num_instruments} stocks")
for row in result.rows:
    print(f"  {row.get('Symbol')} - {row.get('CompanyName')}")
```

!!! note

    `run_screen()` uses predefined screen names (not user-saved screen names). User-saved screens from `get_screens()` contain metadata but cannot be directly dispatched through `run_screen()`.

## Predefined reports

MarketSurge provides a catalog of predefined stock lists like "Bases Forming", "Breaking Out Today", and "RS Line Blue Dot".

### List all reports

```python
reports = client.get_reports()
for report in reports:
    print(f"{report.name} (ID: {report.original_id})")
```

The full list includes reports like:

| Report | ID |
|--------|----|
| Bases Forming | 124 |
| Breaking Out Today | 104 |
| Near Pivot | 106 |
| RS Line Blue Dot | 121 |
| Minervini Trend - 1 Month | 119 |
| Top Rated Stocks | 88 |
| MarketSurge Growth 250 | 93 |
| Earnings - Upcoming | 113 |

See the [API Reference][tickerscope.PREDEFINED_REPORTS] for the complete list.

### Run a report by name

```python
result = await client.run_report_by_name("Bases Forming")
for entry in result.entries:
    print(f"{entry.symbol} - {entry.company_name}, RS: {entry.rs_rating}")
```

### Run a report by ID

```python
result = await client.run_report(124)  # Bases Forming
```

## Coach account screens

Coach screens are curated stock screens from well-known investors (e.g. "William J. O'Neil", "Warren Buffett").

### Browse the coach tree

```python
coach = await client.get_coach_lists()

# Coach data has two sub-trees: screens and watchlists
# Each tree uses NavTreeFolder/NavTreeLeaf nodes
```

### Run a coach screen by name

```python
result = await client.run_coach_screen_by_name("William J. O'Neil - Stock Screen")
print(f"Found {result.num_instruments} stocks")
```

### Run a coach screen by ID

If you already have the opaque screen ID from the coach tree:

```python
result = await client.run_coach_screen("some-opaque-screen-id")
```

## Catalog: discover everything at once

`get_catalog()` aggregates all discoverable stock lists into a single unified collection. It combines user screens, predefined reports, coach screens, and watchlists:

```python
catalog = await client.get_catalog()

print(f"Total entries: {len(catalog.entries)}")
for entry in catalog.entries:
    print(f"  [{entry.kind}] {entry.name}")

# Any errors during discovery
for error in catalog.errors:
    print(f"Warning: {error}")
```

Each [`CatalogEntry`][tickerscope.CatalogEntry] has a `kind` field (`"screen"`, `"report"`, `"coach_screen"`, or `"watchlist"`) and carries the ID needed to run it.

### Run a catalog entry

```python
# Find a report entry
report_entry = next(
    e for e in catalog.entries
    if e.kind == "report" and e.name == "Bases Forming"
)

result = await client.run_catalog_entry(report_entry)
print(result.kind)  # "report"

# Result is wrapped in CatalogResult with one populated field:
if result.adhoc_result:
    for entry in result.adhoc_result.entries:
        print(entry.symbol)
```

!!! note

    Screen entries (`kind="screen"`) cannot be dispatched through `run_catalog_entry()` because user-saved screens require fully-qualified predefined screen names and parameters. Use `run_screen()` directly for those.

## Alerts

### Active alert subscriptions

```python
alerts = await client.get_active_alerts()
print(f"{alerts.num_subscriptions} active, "
      f"{alerts.remaining_subscriptions} remaining")

for sub in alerts.subscriptions:
    if sub.criteria and sub.criteria.term:
        term = sub.criteria.term
        ticker = term.instrument.ticker if term.instrument else "N/A"
        print(f"  {ticker}: {term.field} {term.operator} {term.value}")
```

### Triggered alerts

```python
triggered = await client.get_triggered_alerts()
for alert in triggered.alerts:
    if alert.term and alert.term.instrument:
        print(f"{alert.term.instrument.ticker}: "
              f"{alert.alert_type} at {alert.create_date}")
```
