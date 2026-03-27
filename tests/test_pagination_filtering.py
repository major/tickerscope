"""Tests for pagination, filtering, and field selection features."""

from __future__ import annotations

# pyright: reportMissingImports=false

from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

from tickerscope._client import (
    _filter_watchlist_entries,
    _paginate_list,
)
from tickerscope._models import (
    AdhocScreenResult,
    CatalogEntry,
    CatalogResult,
    Ratings,
    ScreenResult,
    WatchlistEntry,
)
from tickerscope._serialization import SerializableDataclass


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _make_entry(
    symbol: str = "AAPL",
    composite_rating: int | None = 95,
    rs_rating: int | None = 89,
    instrument_sub_type: str | None = None,
    **overrides: object,
) -> WatchlistEntry:
    """Build a WatchlistEntry with sensible defaults."""
    defaults: dict = dict(
        symbol=symbol,
        company_name=f"{symbol} Inc.",
        list_rank=1,
        price=100.0,
        price_net_change=1.5,
        price_pct_change=1.5,
        price_pct_off_52w_high=-5.0,
        volume=1_000_000,
        volume_change=100_000,
        volume_pct_change=10.0,
        composite_rating=composite_rating,
        eps_rating=90,
        rs_rating=rs_rating,
        acc_dis_rating="B+",
        smr_rating="A",
        industry_group_rank=10,
        industry_name="Technology",
        instrument_sub_type=instrument_sub_type,
    )
    defaults.update(overrides)
    return WatchlistEntry(**defaults)


def _make_entries(count: int) -> list[WatchlistEntry]:
    """Build a list of numbered WatchlistEntry objects."""
    return [
        _make_entry(
            symbol=f"SYM{i}",
            composite_rating=90 - i,
            rs_rating=85 - i,
            list_rank=i,
        )
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# _paginate_list tests
# ---------------------------------------------------------------------------


class TestPaginateList:
    """Tests for the _paginate_list helper function."""

    def test_no_pagination_returns_full_list(self):
        """No limit or offset returns the original list unchanged."""
        items = [1, 2, 3, 4, 5]
        assert _paginate_list(items, limit=None, offset=None) == items

    def test_limit_only(self):
        """Limit without offset returns first N items."""
        items = [1, 2, 3, 4, 5]
        assert _paginate_list(items, limit=3, offset=None) == [1, 2, 3]

    def test_offset_only(self):
        """Offset without limit skips first N items."""
        items = [1, 2, 3, 4, 5]
        assert _paginate_list(items, limit=None, offset=2) == [3, 4, 5]

    def test_limit_and_offset(self):
        """Both limit and offset slice the correct window."""
        items = [1, 2, 3, 4, 5]
        assert _paginate_list(items, limit=2, offset=1) == [2, 3]

    def test_offset_beyond_length(self):
        """Offset past the end returns empty list."""
        items = [1, 2, 3]
        assert _paginate_list(items, limit=10, offset=100) == []

    def test_limit_exceeds_remaining(self):
        """Limit larger than remaining items returns all remaining."""
        items = [1, 2, 3]
        assert _paginate_list(items, limit=10, offset=1) == [2, 3]

    def test_empty_list(self):
        """Pagination on empty list returns empty list."""
        assert _paginate_list([], limit=5, offset=0) == []

    def test_zero_limit(self):
        """Limit of zero returns empty list."""
        assert _paginate_list([1, 2, 3], limit=0, offset=0) == []

    def test_zero_offset(self):
        """Explicit zero offset is same as no offset."""
        items = [1, 2, 3]
        assert _paginate_list(items, limit=2, offset=0) == [1, 2]


# ---------------------------------------------------------------------------
# _filter_watchlist_entries tests
# ---------------------------------------------------------------------------


class TestFilterWatchlistEntries:
    """Tests for the _filter_watchlist_entries helper function."""

    def test_numeric_threshold_single_field(self):
        """Filter by composite_rating >= 85 keeps only qualifying entries."""
        entries = [
            _make_entry(symbol="HIGH", composite_rating=90),
            _make_entry(symbol="MID", composite_rating=85),
            _make_entry(symbol="LOW", composite_rating=70),
        ]
        result = _filter_watchlist_entries(entries, {"composite_rating": 85})
        symbols = [e.symbol for e in result]
        assert symbols == ["HIGH", "MID"]

    def test_numeric_threshold_multiple_fields(self):
        """Multiple threshold filters are applied as AND conditions."""
        entries = [
            _make_entry(symbol="BOTH", composite_rating=90, rs_rating=80),
            _make_entry(symbol="ONE", composite_rating=90, rs_rating=50),
            _make_entry(symbol="NEITHER", composite_rating=50, rs_rating=50),
        ]
        result = _filter_watchlist_entries(
            entries, {"composite_rating": 80, "rs_rating": 70}
        )
        assert [e.symbol for e in result] == ["BOTH"]

    def test_none_field_excluded_by_threshold(self):
        """Entries with None for a filtered field are excluded."""
        entries = [
            _make_entry(symbol="GOOD", composite_rating=90),
            _make_entry(symbol="NONE", composite_rating=None),
        ]
        result = _filter_watchlist_entries(entries, {"composite_rating": 80})
        assert [e.symbol for e in result] == ["GOOD"]

    def test_exclude_instrument_sub_type(self):
        """Exclusion filter removes entries matching specified sub-types."""
        entries = [
            _make_entry(symbol="STOCK", instrument_sub_type="COMMON"),
            _make_entry(symbol="SPAC", instrument_sub_type="BLANK_CHECK"),
            _make_entry(symbol="ETF", instrument_sub_type="ETF"),
        ]
        result = _filter_watchlist_entries(
            entries, {"exclude_instrument_sub_type": ["BLANK_CHECK", "ETF"]}
        )
        assert [e.symbol for e in result] == ["STOCK"]

    def test_combined_threshold_and_exclusion(self):
        """Threshold and exclusion filters work together."""
        entries = [
            _make_entry(
                symbol="KEEP", composite_rating=90, instrument_sub_type="COMMON"
            ),
            _make_entry(
                symbol="LOW", composite_rating=50, instrument_sub_type="COMMON"
            ),
            _make_entry(
                symbol="SPAC", composite_rating=95, instrument_sub_type="BLANK_CHECK"
            ),
        ]
        result = _filter_watchlist_entries(
            entries,
            {"composite_rating": 80, "exclude_instrument_sub_type": ["BLANK_CHECK"]},
        )
        assert [e.symbol for e in result] == ["KEEP"]

    def test_empty_entries(self):
        """Filtering empty list returns empty list."""
        assert _filter_watchlist_entries([], {"composite_rating": 80}) == []

    def test_no_matches(self):
        """Filter that excludes everything returns empty list."""
        entries = [_make_entry(composite_rating=50)]
        assert _filter_watchlist_entries(entries, {"composite_rating": 99}) == []

    def test_unknown_field_excludes_all(self):
        """Threshold on a nonexistent field excludes all entries (getattr returns None)."""
        entries = [_make_entry()]
        result = _filter_watchlist_entries(entries, {"nonexistent_field": 1})
        assert result == []


# ---------------------------------------------------------------------------
# to_dict field selection tests
# ---------------------------------------------------------------------------


class TestToDictFieldSelection:
    """Tests for the fields parameter on to_dict() and to_json()."""

    def test_fields_limits_output(self):
        """Only requested fields appear in to_dict output."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        d = r.to_dict(fields={"composite", "rs"})
        assert d == {"composite": 95, "rs": 89}

    def test_fields_none_returns_all(self):
        """fields=None returns all fields (backward compat)."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        d = r.to_dict(fields=None)
        assert len(d) == 5

    def test_fields_empty_set_returns_empty(self):
        """Empty fields set returns empty dict."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        assert r.to_dict(fields=set()) == {}

    def test_fields_with_omit_none(self):
        """fields and omit_none work together."""
        r = Ratings(composite=95, eps=None, rs=89, smr=None, ad="B+")
        d = r.to_dict(fields={"composite", "eps", "rs"})
        assert d == {"composite": 95, "rs": 89}

    def test_fields_with_omit_none_false(self):
        """fields with omit_none=False includes None values for requested fields."""
        r = Ratings(composite=95, eps=None, rs=89, smr=None, ad="B+")
        d = r.to_dict(fields={"composite", "eps"}, omit_none=False)
        assert d == {"composite": 95, "eps": None}

    def test_fields_unknown_field_ignored(self):
        """Fields not present on the dataclass are silently ignored."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        d = r.to_dict(fields={"composite", "nonexistent"})
        assert d == {"composite": 95}

    def test_fields_recursive_on_list(self):
        """Field filter propagates to nested dataclass lists."""
        entry = _make_entry(symbol="AAPL", composite_rating=95, rs_rating=89)
        result = AdhocScreenResult(entries=[entry], error_values=None)
        d = result.to_dict(fields={"symbol", "composite_rating", "entries"})
        assert "entries" in d
        assert len(d["entries"]) == 1
        entry_dict = d["entries"][0]
        assert set(entry_dict.keys()) == {"symbol", "composite_rating"}

    def test_fields_on_to_json(self):
        """to_json() respects fields parameter."""
        import json

        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        parsed = json.loads(r.to_json(fields={"composite", "rs"}))
        assert parsed == {"composite": 95, "rs": 89}


@dataclass(frozen=True, slots=True)
class _NestedChild(SerializableDataclass):
    """Nested child for recursive field selection tests."""

    x: int
    y: int


@dataclass(frozen=True, slots=True)
class _NestedParent(SerializableDataclass):
    """Parent with nested child for recursive field selection tests."""

    name: str
    child: _NestedChild


class TestToDictFieldSelectionNested:
    """Tests for recursive field selection on nested dataclasses."""

    def test_fields_on_nested_child(self):
        """Field filter applies to nested dataclass children."""
        parent = _NestedParent(name="p", child=_NestedChild(x=1, y=2))
        d = parent.to_dict(fields={"name", "child", "x"})
        assert d == {"name": "p", "child": {"x": 1}}

    def test_fields_excludes_nested_entirely(self):
        """When 'child' is not in fields, nested object is excluded."""
        parent = _NestedParent(name="p", child=_NestedChild(x=1, y=2))
        d = parent.to_dict(fields={"name"})
        assert d == {"name": "p"}


# ---------------------------------------------------------------------------
# Sync run_catalog_entry pagination tests
# ---------------------------------------------------------------------------


class TestRunCatalogEntryPagination:
    """Tests for pagination and filtering on sync run_catalog_entry()."""

    def _mock_report_result(self, sync_client, entries: list[WatchlistEntry]) -> None:
        """Set up sync_client.run_report to return entries."""
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        sync_client.run_report = MagicMock(return_value=adhoc)

    def test_report_limit_only(self, sync_client):
        """Limit on report entries returns first N items with correct total."""
        entries = _make_entries(10)
        self._mock_report_result(sync_client, entries)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e, limit=3)

        assert result.total == 10
        assert len(result.adhoc_result.entries) == 3
        assert result.adhoc_result.entries[0].symbol == "SYM0"

    def test_report_offset_only(self, sync_client):
        """Offset skips entries and total reflects full count."""
        entries = _make_entries(5)
        self._mock_report_result(sync_client, entries)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e, offset=3)

        assert result.total == 5
        assert len(result.adhoc_result.entries) == 2
        assert result.adhoc_result.entries[0].symbol == "SYM3"

    def test_report_limit_and_offset(self, sync_client):
        """Combined limit and offset returns correct page window."""
        entries = _make_entries(10)
        self._mock_report_result(sync_client, entries)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e, limit=3, offset=2)

        assert result.total == 10
        assert len(result.adhoc_result.entries) == 3
        assert result.adhoc_result.entries[0].symbol == "SYM2"

    def test_report_offset_beyond_length(self, sync_client):
        """Offset past end returns empty entries with total reflecting full count."""
        entries = _make_entries(3)
        self._mock_report_result(sync_client, entries)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e, offset=100)

        assert result.total == 3
        assert result.adhoc_result.entries == []

    def test_report_filters_before_pagination(self, sync_client):
        """Filters reduce the set before pagination, total reflects post-filter count."""
        entries = [
            _make_entry(symbol="HIGH", composite_rating=95),
            _make_entry(symbol="MID", composite_rating=85),
            _make_entry(symbol="LOW", composite_rating=50),
        ]
        self._mock_report_result(sync_client, entries)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(
            e, limit=1, filters={"composite_rating": 80}
        )

        assert result.total == 2
        assert len(result.adhoc_result.entries) == 1
        assert result.adhoc_result.entries[0].symbol == "HIGH"

    def test_report_no_pagination_returns_all(self, sync_client):
        """No limit/offset returns all entries with total set."""
        entries = _make_entries(5)
        self._mock_report_result(sync_client, entries)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e)

        assert result.total == 5
        assert len(result.adhoc_result.entries) == 5

    def test_report_empty_result(self, sync_client):
        """Empty report result has total=0."""
        self._mock_report_result(sync_client, [])
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e)

        assert result.total == 0
        assert result.adhoc_result.entries == []

    def test_watchlist_pagination(self, sync_client):
        """Watchlist entries support pagination with total."""
        entries = _make_entries(5)
        sync_client.get_watchlist = MagicMock(return_value=entries)
        e = CatalogEntry(name="My WL", kind="watchlist", watchlist_id=99)

        result = sync_client.run_catalog_entry(e, limit=2, offset=1)

        assert result.total == 5
        assert len(result.watchlist_entries) == 2
        assert result.watchlist_entries[0].symbol == "SYM1"

    def test_watchlist_filters(self, sync_client):
        """Watchlist entries support filtering before pagination."""
        entries = [
            _make_entry(symbol="KEEP", composite_rating=90),
            _make_entry(symbol="DROP", composite_rating=50),
        ]
        sync_client.get_watchlist = MagicMock(return_value=entries)
        e = CatalogEntry(name="My WL", kind="watchlist", watchlist_id=99)

        result = sync_client.run_catalog_entry(e, filters={"composite_rating": 80})

        assert result.total == 1
        assert result.watchlist_entries[0].symbol == "KEEP"

    def test_coach_screen_pagination(self, sync_client):
        """Coach screen results support pagination on rows."""
        rows = [{"Symbol": f"SYM{i}"} for i in range(5)]
        screen_result = ScreenResult(
            screen_name="Buffett",
            elapsed_time="1s",
            num_instruments=5,
            rows=rows,
        )
        sync_client.run_coach_screen = MagicMock(return_value=screen_result)
        e = CatalogEntry(name="Buffett", kind="coach_screen", coach_screen_id="abc")

        result = sync_client.run_catalog_entry(e, limit=2, offset=1)

        assert result.total == 5
        assert len(result.screen_result.rows) == 2
        assert result.screen_result.rows[0]["Symbol"] == "SYM1"

    def test_backward_compat_no_params(self, sync_client):
        """run_catalog_entry without new params works as before."""
        adhoc = AdhocScreenResult(entries=_make_entries(3), error_values=None)
        sync_client.run_report = MagicMock(return_value=adhoc)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = sync_client.run_catalog_entry(e)

        assert isinstance(result, CatalogResult)
        assert result.kind == "report"
        assert result.total == 3


# ---------------------------------------------------------------------------
# Async run_catalog_entry pagination tests
# ---------------------------------------------------------------------------


class TestAsyncRunCatalogEntryPagination:
    """Tests for pagination and filtering on async run_catalog_entry()."""

    async def test_report_limit_and_offset(self, async_client):
        """Async report pagination returns correct page window with total."""
        entries = _make_entries(10)
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        async_client.run_report = AsyncMock(return_value=adhoc)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = await async_client.run_catalog_entry(e, limit=3, offset=2)

        assert result.total == 10
        assert len(result.adhoc_result.entries) == 3
        assert result.adhoc_result.entries[0].symbol == "SYM2"

    async def test_report_filters_with_pagination(self, async_client):
        """Async filtering applies before pagination with correct total."""
        entries = [
            _make_entry(symbol="A", composite_rating=95),
            _make_entry(symbol="B", composite_rating=85),
            _make_entry(symbol="C", composite_rating=50),
        ]
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        async_client.run_report = AsyncMock(return_value=adhoc)
        e = CatalogEntry(name="Test", kind="report", report_id=1)

        result = await async_client.run_catalog_entry(
            e, limit=1, filters={"composite_rating": 80}
        )

        assert result.total == 2
        assert len(result.adhoc_result.entries) == 1

    async def test_watchlist_pagination(self, async_client):
        """Async watchlist pagination returns correct page with total."""
        entries = _make_entries(5)
        async_client.get_watchlist = AsyncMock(return_value=entries)
        e = CatalogEntry(name="WL", kind="watchlist", watchlist_id=1)

        result = await async_client.run_catalog_entry(e, limit=2)

        assert result.total == 5
        assert len(result.watchlist_entries) == 2


# ---------------------------------------------------------------------------
# CatalogResult total field tests
# ---------------------------------------------------------------------------


class TestCatalogResultTotal:
    """Tests for the total field on CatalogResult."""

    def test_total_defaults_to_none(self):
        """CatalogResult without total has None (backward compat)."""
        r = CatalogResult(kind="report")
        assert r.total is None

    def test_total_set_explicitly(self):
        """CatalogResult total can be set to an integer."""
        r = CatalogResult(kind="report", total=42)
        assert r.total == 42

    def test_total_in_to_dict(self):
        """Total appears in to_dict output when set."""
        r = CatalogResult(kind="report", total=10)
        d = r.to_dict()
        assert d["total"] == 10

    def test_total_omitted_when_none(self):
        """Total is omitted from to_dict when None (omit_none default)."""
        r = CatalogResult(kind="report")
        assert "total" not in r.to_dict()


# ---------------------------------------------------------------------------
# Sync run_report and get_watchlist standalone tests
# ---------------------------------------------------------------------------


class TestRunReportStandalone:
    """Tests for standalone run_report() with pagination and filtering."""

    def test_limit(self, sync_client):
        """run_report(limit=N) returns at most N entries."""
        entries = _make_entries(5)
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        sync_client._graphql_and_parse = MagicMock(return_value=adhoc)

        result = sync_client.run_report(1, limit=2)

        assert len(result.entries) == 2

    def test_filters(self, sync_client):
        """run_report(filters=...) applies threshold filters."""
        entries = [
            _make_entry(symbol="KEEP", composite_rating=90),
            _make_entry(symbol="DROP", composite_rating=50),
        ]
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        sync_client._graphql_and_parse = MagicMock(return_value=adhoc)

        result = sync_client.run_report(1, filters={"composite_rating": 80})

        assert len(result.entries) == 1
        assert result.entries[0].symbol == "KEEP"

    def test_no_params_backward_compat(self, sync_client):
        """run_report() without new params returns full result unchanged."""
        entries = _make_entries(3)
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        sync_client._graphql_and_parse = MagicMock(return_value=adhoc)

        result = sync_client.run_report(1)

        assert len(result.entries) == 3

    def test_error_values_preserved(self, sync_client):
        """error_values from the original result carry through pagination."""
        adhoc = AdhocScreenResult(entries=_make_entries(5), error_values=["some error"])
        sync_client._graphql_and_parse = MagicMock(return_value=adhoc)

        result = sync_client.run_report(1, limit=2)

        assert result.error_values == ["some error"]


class TestAsyncRunReportStandalone:
    """Tests for standalone async run_report() with pagination and filtering."""

    async def test_limit_and_offset(self, async_client):
        """Async run_report with limit and offset returns correct page."""
        entries = _make_entries(10)
        adhoc = AdhocScreenResult(entries=entries, error_values=None)
        async_client._graphql_and_parse = AsyncMock(return_value=adhoc)

        result = await async_client.run_report(1, limit=3, offset=2)

        assert len(result.entries) == 3
        assert result.entries[0].symbol == "SYM2"
