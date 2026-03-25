# Missing GraphQL Queries Report

**Generated:** 2026-03-25
**Source:** `full_refresh_daily.har`, `full_refresh_weekly.har`
**Compared against:** tickerscope v0.x (13 implemented queries in `src/tickerscope/queries/`)

## Summary

The HAR files captured from MarketSurge contain **18 unique GraphQL operations**.
tickerscope currently implements **13** of those. **5 are completely missing** and
1 is an alternate variant of an existing query worth noting.

```text
                                        Daily   Weekly
  Operation              Status          HAR     HAR     Priority
  ---------------------------------------------------------------
  OtherMarketData        IMPLEMENTED      x       x
  ChartMarketData        IMPLEMENTED      x       x
  FundermentalDataBox    IMPLEMENTED      x       x
  FetchChartMarkups      IMPLEMENTED      x       x
  ActiveAlerts           IMPLEMENTED      x       x
  TriggeredAlerts        IMPLEMENTED      x       x
  MarketDataLayouts      IMPLEMENTED      x       x
  GetAllWatchlistNames   IMPLEMENTED      x       x
  Screens                IMPLEMENTED      x       x
  MarketDataAdhocScreen  IMPLEMENTED      x       x
  FlaggedSymbols         IMPLEMENTED      x       x
  Ownership              IMPLEMENTED              x
  AllPanels              MISSING          x       x      Medium
  RSRatingRIPanel        MISSING          x       x      High
  GetServerDateTime      MISSING          x       x      Low
  NavTree                MISSING          x       x      Medium
  CoachTree              MISSING          x       x      Medium
  ScreenerAdhoc          VARIANT                  x      Low
```

## Missing Queries

### 1. RSRatingRIPanel

**Priority:** High - provides RS rating history across multiple time periods, critical
for CAN SLIM analysis and trend evaluation.

**What it does:** Fetches RS Rating values at six historical offsets (current, 1W ago,
4W ago, 3M ago, 6M ago, 1Y ago) across multiple periods (P12M, P3M, P6M), plus the
`rsLineNewHigh` boolean indicator.

The existing `OtherMarketData` query only fetches the *current* RS rating
(`where: { periodOffset: { eq: CURRENT } }`). This query returns the full historical
picture that populates the RS Rating panel in the MarketSurge UI.

**Variables:**

```json
{
  "symbols": "13-4698",
  "symbolDialectType": "DJ_KEY"
}
```

Note: `symbols` is passed as a bare string here, not an array, despite the type
declaration being `[String!]!`. The API accepts both forms.

**Query:**

```graphql
query RSRatingRIPanel(
  $symbols: [String!]!
  $symbolDialectType: MDSymbolDialectType!
) {
  marketData(symbols: $symbols, symbolDialectType: $symbolDialectType) {
    id
    ratings {
      rsRating {
        letterValue
        period
        periodOffset
        value
      }
    }
    pricingStatistics {
      intradayStatistics {
        rsLineNewHigh
      }
    }
  }
}
```

**Sample response:**

```json
{
  "data": {
    "marketData": [
      {
        "id": "208144392",
        "ratings": {
          "rsRating": [
            { "letterValue": "NONE", "period": "P12M", "periodOffset": "P4W_AGO",  "value": 87 },
            { "letterValue": "NONE", "period": "P12M", "periodOffset": "P3M_AGO",  "value": 94 },
            { "letterValue": "NONE", "period": "P12M", "periodOffset": "P6M_AGO",  "value": 79 },
            { "letterValue": "NONE", "period": "P12M", "periodOffset": "P1Y_AGO",  "value": 13 },
            { "letterValue": "NONE", "period": "P12M", "periodOffset": "P1W_AGO",  "value": 90 },
            { "letterValue": "NONE", "period": "P12M", "periodOffset": "CURRENT",  "value": 90 },
            { "letterValue": "NONE", "period": "P3M",  "periodOffset": "CURRENT",  "value": 35 },
            { "letterValue": "NONE", "period": "P6M",  "periodOffset": "CURRENT",  "value": 36 }
          ]
        },
        "pricingStatistics": {
          "intradayStatistics": {
            "rsLineNewHigh": false
          }
        }
      }
    ]
  }
}
```

**Suggested method name:** `get_rs_rating_history(symbol)`
**Suggested return type:** New dataclass with list of RS rating snapshots + rsLineNewHigh flag

---

### 2. AllPanels

**Priority:** Medium - contains user settings, current chart state, and layout preferences.

**What it does:** Retrieves all user panel configurations. Each panel stores a
different type of user preference or UI state. The most interesting panel is the
`LAYOUT` type, which contains the currently loaded symbol, chart type, time unit,
and all display toggles.

**Variables:**

```json
{
  "site": "marketsurge"
}
```

**Query:**

```graphql
query AllPanels($site: Site!) {
  user {
    panels(site: $site) {
      id
      name
      site
      type
      data
      createdAt
      updatedAt
    }
  }
}
```

**Panel types observed in response:**

| Type | Purpose |
|------|---------|
| `ALERTS_SETTING` | Alert window/audio/email notification prefs |
| `APPLICATION_SETTINGS` | General app settings (empty in sample) |
| `CHARTIQ` | Chart view mode (list/grid), docked state |
| `COLUMNS_WIDTHS` | Per-view column width overrides |
| `LAYOUT` | Current chart state: symbol, timeUnit, chartType, all toggles |

**Sample LAYOUT panel data (truncated):**

```json
{
  "symbol": "NGL",
  "name": "NGL Energy Partners LP",
  "chartSymbol": "STOCK/US/XNYS/NGL",
  "dowJonesKey": "13-4609967",
  "tickerType": "stock",
  "indexSymbol": "0S&P5",
  "indexDowJonesKey": "211-497001",
  "timeUnit": "day",
  "interval": 1,
  "chartType": "hlc_box",
  "showEpsSaleTable": false,
  "showEarnings": false,
  "showMarkups": true
}
```

**Suggested method name:** `get_panels()`
**Suggested return type:** `list[Panel]` with Panel having typed `data` field (or pass-through dict)

---

### 3. NavTree

**Priority:** Medium - provides the full sidebar navigation hierarchy (watchlists,
screens, folders).

**What it does:** Retrieves the user's navigation tree structure. This is the sidebar
tree in MarketSurge that organizes watchlists, screens, and folders into a hierarchy
(Activity Lists, My Lists, My Screens, etc.).

**Variables:**

```json
{
  "site": "marketsurge",
  "treeType": "MSR_NAV"
}
```

**Query:**

```graphql
query NavTree($site: Site!, $treeType: NavTreeTypeInput!) {
  user {
    navTree(site: $site, treeType: $treeType) {
      ... on NavTreeFolder {
        id
        name
        parentId
        type
        children {
          ... on NavTreeFolder {
            id
            name
            type
          }
          ... on NavTreeLeaf {
            id
            name
            type
          }
        }
        contentType
        treeType
      }
      ... on NavTreeLeaf {
        id
        name
        parentId
        type
        url
        treeType
        referenceId
      }
    }
  }
}
```

**Node types observed:**

| `type` value | Description | Where it appears |
|---|---|---|
| `SYSTEM_FOLDER` | Built-in folders | "Activity Lists", "My Lists", "My Screens" |
| `WATCHLIST` | A watchlist leaf | "Flagged Symbols", "Recent Symbols", user lists |
| `STOCK_SCREEN` | A saved screen leaf | User-created/saved screens |

Leaf nodes have a `referenceId` field containing JSON with IDs:

- Watchlists: `{"watchlistId": "266152633632307"}`
- Screens: `{"screenId": "01KJX696Z94RQPXK3EEH62GYNZ"}`

**Suggested method name:** `get_nav_tree()`
**Suggested return type:** `list[NavTreeNode]` (union of NavTreeFolder/NavTreeLeaf)

---

### 4. CoachTree

**Priority:** Medium - provides IBD-curated watchlists and screens (content coaching lists).

**What it does:** Retrieves two separate tree structures in one call: IBD's curated
watchlists (IBD Live Watch, S&P Sectors, etc.) and IBD's curated screens (William J.
O'Neil, etc.). These are the pre-built lists and screens from IBD's coaching program.

**Variables:**

```json
{
  "site": "marketsurge",
  "treeType": "MSR_NAV"
}
```

**Query:**

```graphql
query CoachTree($site: Site!, $treeType: NavTreeTypeInput!) {
  user {
    watchlists: coachTree(
      coachTreeType: WATCHLIST
      site: $site
      treeType: $treeType
    ) {
      ... on NavTreeFolder {
        id
        name
        parentId
        type
        children {
          ... on NavTreeFolder { id name type }
          ... on NavTreeLeaf { id name type }
        }
        contentType
        treeType
      }
      ... on NavTreeLeaf {
        id
        name
        parentId
        type
        url
        treeType
        referenceId
      }
    }
    screens: coachTree(
      coachTreeType: SCREEN
      site: $site
      treeType: $treeType
    ) {
      ... on NavTreeFolder {
        id
        name
        parentId
        type
        children {
          ... on NavTreeFolder { id name type }
          ... on NavTreeLeaf { id name type }
        }
        contentType
        treeType
      }
      ... on NavTreeLeaf {
        id
        name
        parentId
        type
        url
        treeType
        referenceId
      }
    }
  }
}
```

Coach tree leaf `referenceId` values contain both IDs:

```json
{"watchlistId": "94490110509978", "screenId": "01KF1ENSYEXKTCXPWKPRQ4S92N"}
```

**Suggested method name:** `get_coach_lists()`
**Suggested return type:** Dataclass with `watchlists` and `screens` fields,
each a `list[NavTreeNode]`

---

### 5. GetServerDateTime

**Priority:** Low - simple server time query, useful for time sync but not essential.

**What it does:** Returns the API server's current UTC timestamp.

**Variables:** None

**Query:**

```graphql
query GetServerDateTime {
  ibdGetServerDateTime
}
```

**Sample response:**

```json
{
  "data": {
    "ibdGetServerDateTime": "2026-03-24T22:10:37.629Z"
  }
}
```

**Suggested method name:** `get_server_time()`
**Suggested return type:** `datetime` (timezone-aware UTC)

---

## Query Variant: ScreenerAdhoc

**Priority:** Low - functionally identical to the existing `MarketDataAdhocScreen`
but uses a different GraphQL operation name and has minor type strictness differences.

**What it is:** The MarketSurge webapp uses two operation names for the same underlying
`marketDataAdhocScreen` GraphQL field:

- `MarketDataAdhocScreen` - used for watchlist data grids (implemented in tickerscope)
- `ScreenerAdhoc` - used for inline screener queries (e.g., "Top RS in Group" panel)

**Differences from existing MarketDataAdhocScreen:**

```text
                     MarketDataAdhocScreen      ScreenerAdhoc
                     (adhoc_screen.graphql)      (HAR only)
  -----------------------------------------------------------------
  $pageSkip type     Int  (optional)             Int! (required)
  $resultType type   MDScreenerResultType        MDScreenerResultType
  errorValues field  NOT selected                SELECTED
  __typename fields  NOT selected                SELECTED
```

**Full query:**

```graphql
query ScreenerAdhoc(
  $correlationTag: String!
  $adhocQuery: MDAdhocQueryInput
  $responseColumns: [MDAdhocScreenerDataItemInput!]!
  $resultLimit: Int!
  $pageSize: Int!
  $pageSkip: Int!
  $resultType: MDScreenerResultType
  $includeSource: MDScreenerDataSourceInput!
) {
  marketDataAdhocScreen(
    correlationTag: $correlationTag
    adhocQuery: $adhocQuery
    resultLimit: $resultLimit
    pageSize: $pageSize
    pageSkip: $pageSkip
    resultType: $resultType
    includeSource: $includeSource
    responseDataPoints: $responseColumns
  ) {
    correlationTag
    elapsedTime
    errorValues
    responseValues {
      value
      mdItem {
        mdItemID
        name
      }
    }
  }
}
```

**Sample variables (industry-filtered screen):**

```json
{
  "correlationTag": "Top RS in Group",
  "resultLimit": 5,
  "pageSize": 5,
  "pageSkip": 0,
  "resultType": "RESULTS_ONLY",
  "includeSource": { "source": "IBD_STOCKS" },
  "adhocQuery": {
    "type": "AND",
    "terms": [
      { "left": { "name": "industries" }, "right": { "value": "Elec-Semicondctor Fablss" }, "operand": "EQUAL" },
      { "left": { "name": "industriesInclusive" }, "operand": "EQUAL", "right": { "value": "true" } }
    ]
  },
  "responseColumns": [
    { "name": "Symbol" },
    { "name": "CompanyName" },
    { "name": "RSRating", "sortInformation": { "direction": "DESCENDING", "order": "PRIMARY" } },
    { "name": "EPSRating" },
    { "name": "CompositeRating" },
    { "name": "DowJonesKey" },
    { "name": "DowJonesInstrumentType" },
    { "name": "ChartingSymbol" }
  ]
}
```

**Recommendation:** Consider adding `errorValues` to the existing `adhoc_screen.graphql`
rather than creating a separate query file. The only real difference is that field
selection. Making `$pageSkip` required (Int!) in the existing query would also match
the stricter variant.

---

## Notable Observations

### ChartMarketData: daily vs weekly variants

The webapp sends two different query shapes depending on chart periodicity:

**Daily charts** (current tickerscope implementation):

```graphql
query ChartMarketData(
  $symbols: [String!]!
  $symbolDialectType: MDSymbolDialectType!
  $where: TimeSeriesFilterInput!
  $exchangeName: String!        # <-- included
) {
  marketData(...) { ... }
  exchangeData(exchangeName: $exchangeName) {   # <-- fetches holidays
    city countryCode exchangeISO id
    holidays(...) { name holidayType description startDateTime endDateTime }
  }
}
```

**Weekly charts** (HAR only, not implemented):

```graphql
query ChartMarketData(
  $symbols: [String!]!
  $symbolDialectType: MDSymbolDialectType!
  $where: TimeSeriesFilterInput!
                                # <-- no $exchangeName
) {
  marketData(...) { ... }
                                # <-- no exchangeData section
}
```

The weekly variant omits the `exchangeData` section entirely (exchange holidays
are irrelevant for weekly candles). tickerscope currently always fetches exchange
data regardless of periodicity. This is not a bug, but it does fetch unnecessary
data for weekly chart requests.

**Recommendation:** Consider making `exchangeName` optional, or splitting into
two query files. Low priority since the current behavior still works correctly.

### Hardcoded holiday date range

The `chart_market_data.graphql` file has hardcoded dates in the exchange holidays
filter:

```graphql
holidays(
  where: {
    startDateTime: { gt: "2021-12-02T07:00:00.000Z" }
    endDateTime: { lt: "2026-03-27T23:55:25.000Z" }
  }
)
```

The HAR files show similar hardcoding. These dates should ideally be parameterized
or dynamically generated based on the chart's date range, but since the upstream
webapp does the same thing, this is just a maintenance note.

---

## Implementation Priority

| Priority | Query | Effort | Value |
|----------|-------|--------|-------|
| High | RSRatingRIPanel | Low (simple query, new model + parser) | RS trend analysis |
| Medium | NavTree | Medium (recursive tree structure) | Sidebar navigation |
| Medium | CoachTree | Medium (dual tree, shares NavTree types) | IBD curated content |
| Medium | AllPanels | Low (simple query, pass-through data) | User state/prefs |
| Low | GetServerDateTime | Trivial (no model needed) | Time sync |
| Low | ScreenerAdhoc (variant) | Trivial (add errorValues to existing) | Error reporting |

The RSRatingRIPanel query is the highest-value addition since it provides data
that isn't available through any existing tickerscope method. The current
`get_stock()` call only returns the *current* RS rating, while this query returns
the full historical trend that powers the RS Rating panel in the MarketSurge UI.
