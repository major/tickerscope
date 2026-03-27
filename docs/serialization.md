# Serialization

All tickerscope data models are frozen dataclasses that inherit from [`SerializableDataclass`][tickerscope.SerializableDataclass], providing built-in dict and JSON serialization.

## Converting to dict

```python
stock = client.get_stock("AAPL")
data = stock.to_dict()
```

By default, `to_dict()` omits fields with `None` values to keep output clean. Pass `omit_none=False` to include everything:

```python
# Include None fields
data = stock.to_dict(omit_none=False)
```

Nested dataclasses are recursively converted:

```python
data = stock.to_dict()
print(data["ratings"]["composite"])  # 95
print(data["company"]["name"])       # "NVIDIA Corp"
```

## Converting to JSON

```python
json_str = stock.to_json()

# With None fields included
json_str = stock.to_json(omit_none=False)
```

## Reconstructing from dict

Use `from_dict()` to reconstruct a model from a dictionary. Nested dataclasses are automatically coerced based on type hints:

```python
from tickerscope import StockData

data = stock.to_dict()
reconstructed = StockData.from_dict(data)

# The reconstructed object is identical
print(reconstructed.ratings.composite)
print(reconstructed.company.name)
```

This is useful for caching or persisting data:

```python
import json

# Save
with open("stock_data.json", "w") as f:
    f.write(stock.to_json())

# Load
with open("stock_data.json") as f:
    data = json.load(f)
    stock = StockData.from_dict(data)
```

## Date properties

String date fields throughout the models have corresponding `_dt` properties that return parsed Python date or datetime objects. The naming convention is consistent: append `_dt` to the field name.

### Date fields (return `datetime.date | None`)

```python
stock = client.get_stock("AAPL")

# String value
print(stock.company.ipo_date)     # "1980-12-12"
# Parsed date object
print(stock.company.ipo_date_dt)  # datetime.date(1980, 12, 12)

# Financials dates
print(stock.financials.eps_due_date)     # "2025-05-01"
print(stock.financials.eps_due_date_dt)  # datetime.date(2025, 5, 1)

# Pattern dates
pattern = stock.patterns[0]
print(pattern.pivot_date)     # "2025-03-10"
print(pattern.pivot_date_dt)  # datetime.date(2025, 3, 10)
```

### Datetime fields (return `datetime.datetime | None`)

Timestamps with time components return timezone-aware datetime objects:

```python
chart = client.get_chart_data("AAPL", lookback="1W")

point = chart.time_series.data_points[0]
print(point.start_date_time)     # "2025-03-20T00:00:00Z"
print(point.start_date_time_dt)  # datetime.datetime(2025, 3, 20, 0, 0, tzinfo=...)
```

### Date list fields

Some fields contain lists of dates (e.g., blue dot event dates):

```python
# String list
print(stock.pricing.blue_dot_daily_dates)     # ["2025-03-15", "2025-03-10"]
# Parsed date list
print(stock.pricing.blue_dot_daily_dates_dt)  # [datetime.date(...), ...]
```

### Common `_dt` properties by model

| Model | Field | Property | Returns |
|-------|-------|----------|---------|
| `Company` | `ipo_date` | `ipo_date_dt` | `date` |
| `Financials` | `eps_due_date` | `eps_due_date_dt` | `date` |
| `Pattern` | `pivot_date` | `pivot_date_dt` | `date` |
| `Pattern` | `base_start_date` | `base_start_date_dt` | `date` |
| `DataPoint` | `start_date_time` | `start_date_time_dt` | `datetime` |
| `Quote` | `trade_date_time` | `trade_date_time_dt` | `datetime` |
| `WatchlistSummary` | `last_modified` | `last_modified_dt` | `datetime` |
| `AlertSubscription` | `create_date` | `create_date_dt` | `datetime` |

!!! tip

    All datetimes returned by `_dt` properties are timezone-aware. tickerscope never returns naive datetime objects.

## Frozen dataclasses

All models are frozen (`@dataclass(frozen=True)`) with `__slots__`, meaning:

- Fields cannot be reassigned after creation
- Instances are hashable and can be used in sets or as dict keys
- Memory footprint is smaller than regular dataclasses

```python
stock = client.get_stock("AAPL")

# This raises FrozenInstanceError:
# stock.symbol = "MSFT"

# Create modified copies using dataclasses.replace:
import dataclasses
modified = dataclasses.replace(stock, symbol="MSFT")
```
