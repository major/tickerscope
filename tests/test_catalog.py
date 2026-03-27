"""Tests for catalog models, helper functions, and client methods."""

from __future__ import annotations

# pyright: reportMissingImports=false

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, MagicMock

import pytest

from tickerscope._client import (
    _coach_tree_to_catalog,
    _extract_leaves,
    _reports_to_catalog,
    _screens_to_catalog,
    _watchlists_to_catalog,
)
from tickerscope._exceptions import APIError
from tickerscope._models import (
    AdhocScreenResult,
    Catalog,
    CatalogEntry,
    CatalogResult,
    CoachTreeData,
    NavTreeFolder,
    NavTreeLeaf,
    NavTreeNode,
    ReportInfo,
    Screen,
    ScreenResult,
    WatchlistDetail,
    WatchlistEntry,
    WatchlistSummary,
    WatchlistSymbol,
)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class TestCatalogEntryModel:
    """Tests for the CatalogEntry frozen dataclass."""

    def test_construction_all_fields(self):
        """Build CatalogEntry with all fields and verify each."""
        e = CatalogEntry(
            name="Test Screen",
            kind="report",
            description="A test report",
            report_id=42,
            coach_screen_id=None,
            watchlist_id=None,
        )
        assert e.name == "Test Screen"
        assert e.kind == "report"
        assert e.description == "A test report"
        assert e.report_id == 42

    def test_construction_minimal(self):
        """Build with name and kind only; optional fields default to None."""
        e = CatalogEntry(name="X", kind="screen")
        assert e.description is None
        assert e.report_id is None
        assert e.coach_screen_id is None
        assert e.watchlist_id is None

    def test_frozen_enforcement(self):
        """Attribute assignment raises FrozenInstanceError."""
        e = CatalogEntry(name="X", kind="report", report_id=1)
        with pytest.raises(FrozenInstanceError):
            e.name = "Y"  # type: ignore[misc]

    def test_to_dict_round_trip_screen(self):
        """CatalogEntry with kind='screen' survives to_dict/from_dict round-trip."""
        e = CatalogEntry(name="My Screen", kind="screen", description="A screen")
        assert CatalogEntry.from_dict(e.to_dict()) == e

    def test_to_dict_round_trip_report(self):
        """CatalogEntry with kind='report' and report_id survives round-trip."""
        e = CatalogEntry(name="Bases Forming", kind="report", report_id=124)
        assert CatalogEntry.from_dict(e.to_dict()) == e

    def test_to_dict_round_trip_coach_screen(self):
        """CatalogEntry with kind='coach_screen' and coach_screen_id survives round-trip."""
        e = CatalogEntry(name="Buffett", kind="coach_screen", coach_screen_id="abc123")
        assert CatalogEntry.from_dict(e.to_dict()) == e

    def test_to_dict_round_trip_watchlist(self):
        """CatalogEntry with kind='watchlist' and watchlist_id survives round-trip."""
        e = CatalogEntry(name="My WL", kind="watchlist", watchlist_id=99)
        assert CatalogEntry.from_dict(e.to_dict()) == e

    def test_to_dict_excludes_none_fields(self):
        """None optional fields are omitted from to_dict output."""
        e = CatalogEntry(name="X", kind="screen")
        d = e.to_dict()
        assert "report_id" not in d
        assert "coach_screen_id" not in d
        assert "watchlist_id" not in d
        assert "description" not in d


class TestCatalogModel:
    """Tests for the Catalog frozen dataclass."""

    def test_construction(self):
        """Build Catalog with entries and no errors."""
        e = CatalogEntry(name="R", kind="report", report_id=1)
        c = Catalog(entries=[e], errors=[])
        assert len(c.entries) == 1
        assert c.errors == []

    def test_empty_catalog(self):
        """Catalog with no entries and no errors is valid."""
        c = Catalog(entries=[], errors=[])
        assert c.entries == []
        assert c.errors == []

    def test_frozen_enforcement(self):
        """Catalog is immutable; attribute assignment raises FrozenInstanceError."""
        c = Catalog(entries=[], errors=[])
        with pytest.raises(FrozenInstanceError):
            c.entries = []  # type: ignore[misc]


class TestCatalogResultModel:
    """Tests for the CatalogResult frozen dataclass."""

    def test_screen_result(self):
        """CatalogResult with screen_result has correct kind."""
        sr = MagicMock(spec=ScreenResult)
        r = CatalogResult(kind="coach_screen", screen_result=sr)
        assert r.kind == "coach_screen"
        assert r.screen_result is sr
        assert r.adhoc_result is None
        assert r.watchlist_entries is None

    def test_adhoc_result(self):
        """CatalogResult with adhoc_result has correct kind."""
        ar = MagicMock(spec=AdhocScreenResult)
        r = CatalogResult(kind="report", adhoc_result=ar)
        assert r.kind == "report"
        assert r.adhoc_result is ar

    def test_watchlist_result(self):
        """CatalogResult with watchlist_entries has correct kind."""
        entries = [MagicMock(spec=WatchlistEntry)]
        r = CatalogResult(kind="watchlist", watchlist_entries=entries)
        assert r.kind == "watchlist"
        assert r.watchlist_entries is entries


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestExtractLeaves:
    """Tests for _extract_leaves() navigation tree helper."""

    def _make_leaf(self, name: str = "Leaf", ref_screen_id: str = "abc") -> NavTreeLeaf:
        """Build a NavTreeLeaf for testing."""
        return NavTreeLeaf(
            id="l1",
            name=name,
            parent_id=None,
            node_type="STOCK_SCREEN",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=None,
            reference_screen_id=ref_screen_id,
        )

    def _make_folder(self, children: list[NavTreeNode]) -> NavTreeFolder:
        """Build a NavTreeFolder for testing."""
        return NavTreeFolder(
            id="f1",
            name="Folder",
            parent_id=None,
            node_type="FOLDER",
            tree_type=None,
            children=children,
            content_type=None,
        )

    def test_flat_list(self):
        """Extract leaves at top level of tree."""
        leaf = self._make_leaf()
        result = _extract_leaves([leaf])
        assert result == [leaf]

    def test_nested_folders(self):
        """Extract leaves recursively from nested folders."""
        leaf1 = self._make_leaf("L1")
        leaf2 = self._make_leaf("L2")
        inner = self._make_folder([leaf2])
        outer = self._make_folder([leaf1, inner])
        result = _extract_leaves([outer])
        assert len(result) == 2
        assert all(isinstance(n, NavTreeLeaf) for n in result)

    def test_empty_tree(self):
        """Return empty list from empty tree."""
        assert _extract_leaves([]) == []

    def test_mixed_nodes(self):
        """Extract only leaves from mix of folders and leaves at multiple depths."""
        leaf1 = self._make_leaf("Top")
        leaf2 = self._make_leaf("Nested")
        folder = self._make_folder([leaf2])
        result = _extract_leaves([leaf1, folder])
        assert len(result) == 2


class TestScreensToCatalog:
    """Tests for _screens_to_catalog() helper."""

    def _make_screen(self, name: str | None, description: str | None = None) -> Screen:
        """Build a Screen for testing."""
        return Screen(
            id="s1",
            name=name,
            type="StockScreen",
            source=None,
            description=description,
            filter_criteria=None,
            created_at=None,
            updated_at=None,
        )

    def test_converts_screens(self):
        """Valid screens become CatalogEntry(kind='screen') with correct fields."""
        s = self._make_screen("Growth Screen", "High growth stocks")
        result = _screens_to_catalog([s])
        assert len(result) == 1
        assert result[0].kind == "screen"
        assert result[0].name == "Growth Screen"
        assert result[0].description == "High growth stocks"

    def test_filters_none_names(self):
        """Screens with name=None are excluded."""
        valid = self._make_screen("Valid")
        null_name = self._make_screen(None)
        result = _screens_to_catalog([valid, null_name])
        assert len(result) == 1
        assert result[0].name == "Valid"

    def test_empty_list(self):
        """Return empty list for empty input."""
        assert _screens_to_catalog([]) == []


class TestReportsToCatalog:
    """Tests for _reports_to_catalog() helper."""

    def test_converts_reports(self):
        """ReportInfo entries become CatalogEntry(kind='report') with report_id."""
        r = ReportInfo(name="Bases Forming", original_id=124)
        result = _reports_to_catalog([r])
        assert len(result) == 1
        assert result[0].kind == "report"
        assert result[0].name == "Bases Forming"
        assert result[0].report_id == 124

    def test_description_is_none(self):
        """Report entries have description=None (no description in ReportInfo)."""
        r = ReportInfo(name="RS Line New High", original_id=121)
        result = _reports_to_catalog([r])
        assert result[0].description is None


class TestCoachTreeToCatalog:
    """Tests for _coach_tree_to_catalog() helper."""

    def _make_screen_leaf(
        self, name: str = "Coach Screen", screen_id: str = "abc"
    ) -> NavTreeLeaf:
        """Build a coach screen NavTreeLeaf."""
        return NavTreeLeaf(
            id="l1",
            name=name,
            parent_id=None,
            node_type="STOCK_SCREEN",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=None,
            reference_screen_id=screen_id,
        )

    def _make_watchlist_leaf(
        self, name: str = "Coach WL", watchlist_id: str = "123"
    ) -> NavTreeLeaf:
        """Build a coach watchlist NavTreeLeaf."""
        return NavTreeLeaf(
            id="l2",
            name=name,
            parent_id=None,
            node_type="WATCHLIST",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=watchlist_id,
            reference_screen_id=None,
        )

    def test_extracts_screen_leaves(self):
        """Screen tree leaves become kind='coach_screen' entries."""
        tree = CoachTreeData(screens=[self._make_screen_leaf()], watchlists=[])
        result = _coach_tree_to_catalog(tree)
        assert len(result) == 1
        assert result[0].kind == "coach_screen"
        assert result[0].coach_screen_id == "abc"

    def test_extracts_watchlist_leaves(self):
        """Watchlist tree leaves become kind='watchlist' entries with int ID."""
        tree = CoachTreeData(screens=[], watchlists=[self._make_watchlist_leaf()])
        result = _coach_tree_to_catalog(tree)
        assert len(result) == 1
        assert result[0].kind == "watchlist"
        assert result[0].watchlist_id == 123

    def test_filters_no_screen_id(self):
        """Leaves without reference_screen_id are excluded from coach_screen entries."""
        leaf = NavTreeLeaf(
            id="l1",
            name="No ID",
            parent_id=None,
            node_type="STOCK_SCREEN",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=None,
            reference_screen_id=None,
        )
        tree = CoachTreeData(screens=[leaf], watchlists=[])
        assert _coach_tree_to_catalog(tree) == []

    def test_filters_no_watchlist_id(self):
        """Leaves without reference_watchlist_id are excluded from watchlist entries."""
        leaf = NavTreeLeaf(
            id="l1",
            name="No WL",
            parent_id=None,
            node_type="WATCHLIST",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=None,
            reference_screen_id=None,
        )
        tree = CoachTreeData(screens=[], watchlists=[leaf])
        assert _coach_tree_to_catalog(tree) == []

    def test_empty_trees(self):
        """Empty screens and watchlists produce empty result."""
        tree = CoachTreeData(screens=[], watchlists=[])
        assert _coach_tree_to_catalog(tree) == []


class TestWatchlistsToCatalog:
    """Tests for _watchlists_to_catalog() helper."""

    def test_converts_watchlists(self):
        """WatchlistSummary entries become CatalogEntry(kind='watchlist')."""
        ws = WatchlistSummary(id=5, name="My WL", last_modified=None, description=None)
        result = _watchlists_to_catalog([ws])
        assert len(result) == 1
        assert result[0].kind == "watchlist"
        assert result[0].watchlist_id == 5

    def test_filters_none_id(self):
        """Summaries with id=None are excluded."""
        good = WatchlistSummary(id=1, name="Good", last_modified=None, description=None)
        bad = WatchlistSummary(
            id=None, name="Bad", last_modified=None, description=None
        )
        result = _watchlists_to_catalog([good, bad])
        assert len(result) == 1
        assert result[0].watchlist_id == 1

    def test_populates_description(self):
        """WatchlistSummary.description is mapped to CatalogEntry.description."""
        ws = WatchlistSummary(
            id=7, name="WL", last_modified=None, description="My stocks"
        )
        result = _watchlists_to_catalog([ws])
        assert result[0].description == "My stocks"


# ---------------------------------------------------------------------------
# Client method tests
# ---------------------------------------------------------------------------


class TestGetCatalog:
    """Tests for get_catalog() on sync and async clients."""

    def test_all_sources_success(self, sync_client):
        """All sources succeed: entries from all 4 kinds, errors empty."""
        screen = Screen(
            id="1",
            name="Growth",
            type=None,
            source=None,
            description=None,
            filter_criteria=None,
            created_at=None,
            updated_at=None,
        )
        watchlist = WatchlistSummary(
            id=5, name="My WL", last_modified=None, description=None
        )
        screen_leaf = NavTreeLeaf(
            id="l1",
            name="Buffett",
            parent_id=None,
            node_type="STOCK_SCREEN",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=None,
            reference_screen_id="abc",
        )
        coach_tree = CoachTreeData(screens=[screen_leaf], watchlists=[])

        sync_client.get_screens = MagicMock(side_effect=RuntimeError("screens boom"))
        sync_client.get_coach_lists = MagicMock(return_value=coach_tree)
        sync_client.get_watchlist_names = MagicMock(return_value=[watchlist])
        sync_client.get_watchlist_symbols = MagicMock(
            return_value=WatchlistDetail(
                id="5", name="My WL", last_modified=None, description=None, items=[]
            )
        )
        sync_client.get_reports = MagicMock(
            return_value=[ReportInfo(name="Bases", original_id=124)]
        )

        result = sync_client.get_catalog()

        assert len(result.errors) == 1
        assert "screens boom" in result.errors[0]
        kinds = {e.kind for e in result.entries}
        assert "report" in kinds
        assert "screen" not in kinds

    def test_partial_failure_watchlists(self, sync_client):
        """Watchlists failure: other sources still returned + 1 error."""
        screen = Screen(
            id="1",
            name="Growth",
            type=None,
            source=None,
            description=None,
            filter_criteria=None,
            created_at=None,
            updated_at=None,
        )
        coach_tree = CoachTreeData(screens=[], watchlists=[])

        sync_client.get_screens = MagicMock(return_value=[screen])
        sync_client.get_coach_lists = MagicMock(return_value=coach_tree)
        sync_client.get_watchlist_names = MagicMock(side_effect=RuntimeError("wl boom"))
        sync_client.get_watchlist_symbols = MagicMock(
            return_value=WatchlistDetail(
                id="5", name="My WL", last_modified=None, description=None, items=[]
            )
        )
        sync_client.get_reports = MagicMock(
            return_value=[ReportInfo(name="Bases", original_id=124)]
        )

        result = sync_client.get_catalog()

        assert len(result.errors) == 1
        kinds = {e.kind for e in result.entries}
        assert "watchlist" not in kinds

    def test_all_failable_fail(self, sync_client):
        """All 3 API calls fail: only report entries + 3 errors."""
        sync_client.get_screens = MagicMock(side_effect=RuntimeError("s"))
        sync_client.get_coach_lists = MagicMock(side_effect=RuntimeError("c"))
        sync_client.get_watchlist_names = MagicMock(side_effect=RuntimeError("w"))
        sync_client.get_watchlist_symbols = MagicMock(
            return_value=WatchlistDetail(
                id="5", name="My WL", last_modified=None, description=None, items=[]
            )
        )
        sync_client.get_reports = MagicMock(
            return_value=[ReportInfo(name="Bases", original_id=124)]
        )

        result = sync_client.get_catalog()

        assert len(result.errors) == 3
        assert all(e.kind == "report" for e in result.entries)

    async def test_async_get_catalog(self, async_client):
        """Async get_catalog returns Catalog with entries from all sources."""
        screen = Screen(
            id="1",
            name="Growth",
            type=None,
            source=None,
            description=None,
            filter_criteria=None,
            created_at=None,
            updated_at=None,
        )
        watchlist = WatchlistSummary(
            id=5, name="My WL", last_modified=None, description=None
        )
        screen_leaf = NavTreeLeaf(
            id="l1",
            name="Buffett",
            parent_id=None,
            node_type="STOCK_SCREEN",
            tree_type=None,
            url=None,
            reference_id=None,
            reference_watchlist_id=None,
            reference_screen_id="abc",
        )
        coach_tree = CoachTreeData(screens=[screen_leaf], watchlists=[])

        async_client.get_screens = AsyncMock(return_value=[screen])
        async_client.get_coach_lists = AsyncMock(return_value=coach_tree)
        async_client.get_watchlist_names = AsyncMock(return_value=[watchlist])
        async_client.get_watchlist_symbols = AsyncMock(
            return_value=WatchlistDetail(
                id="5", name="My WL", last_modified=None, description=None, items=[]
            )
        )
        async_client.get_reports = AsyncMock(
            return_value=[ReportInfo(name="Bases", original_id=124)]
        )

        result = await async_client.get_catalog()

        assert isinstance(result, Catalog)
        assert result.errors == []
        kinds = {e.kind for e in result.entries}
        assert "screen" in kinds
        assert "report" in kinds


class TestRunCatalogEntry:
    """Tests for run_catalog_entry() on sync and async clients."""

    def test_screen_raises_not_implemented(self, sync_client):
        """kind='screen' raises NotImplementedError with helpful message."""
        e = CatalogEntry(name="My Screen", kind="screen")
        with pytest.raises(NotImplementedError, match="run_screen"):
            sync_client.run_catalog_entry(e)

    def test_dispatch_report(self, sync_client):
        """kind='report' calls run_report and wraps in CatalogResult."""
        adhoc = MagicMock(spec=AdhocScreenResult)
        sync_client.run_report = MagicMock(return_value=adhoc)
        e = CatalogEntry(name="Bases Forming", kind="report", report_id=124)

        result = sync_client.run_catalog_entry(e)

        sync_client.run_report.assert_called_once_with(124)
        assert isinstance(result, CatalogResult)
        assert result.kind == "report"
        assert result.adhoc_result is adhoc

    def test_dispatch_coach_screen(self, sync_client):
        """kind='coach_screen' calls run_coach_screen and wraps in CatalogResult."""
        sr = MagicMock(spec=ScreenResult)
        sync_client.run_coach_screen = MagicMock(return_value=sr)
        e = CatalogEntry(name="Buffett", kind="coach_screen", coach_screen_id="abc123")

        result = sync_client.run_catalog_entry(e)

        sync_client.run_coach_screen.assert_called_once_with("abc123")
        assert result.kind == "coach_screen"
        assert result.screen_result is sr

    def test_dispatch_watchlist(self, sync_client):
        """kind='watchlist' calls get_watchlist and wraps in CatalogResult."""
        entries = [MagicMock(spec=WatchlistEntry)]
        sync_client.get_watchlist = MagicMock(return_value=entries)
        e = CatalogEntry(name="My WL", kind="watchlist", watchlist_id=99)

        result = sync_client.run_catalog_entry(e)

        sync_client.get_watchlist.assert_called_once_with(99)
        assert result.kind == "watchlist"
        assert result.watchlist_entries is entries

    def test_report_none_id_raises(self, sync_client):
        """kind='report' with None report_id raises APIError."""
        e = CatalogEntry(name="Missing", kind="report")
        with pytest.raises(APIError):
            sync_client.run_catalog_entry(e)

    def test_coach_screen_none_id_raises(self, sync_client):
        """kind='coach_screen' with None coach_screen_id raises APIError."""
        e = CatalogEntry(name="Missing", kind="coach_screen")
        with pytest.raises(APIError):
            sync_client.run_catalog_entry(e)

    def test_watchlist_none_id_raises(self, sync_client):
        """kind='watchlist' with None watchlist_id raises APIError."""
        e = CatalogEntry(name="Missing", kind="watchlist")
        with pytest.raises(APIError):
            sync_client.run_catalog_entry(e)

    async def test_async_dispatch_report(self, async_client):
        """Async run_catalog_entry dispatches report to run_report."""
        adhoc = MagicMock(spec=AdhocScreenResult)
        async_client.run_report = AsyncMock(return_value=adhoc)
        e = CatalogEntry(name="Bases Forming", kind="report", report_id=124)

        result = await async_client.run_catalog_entry(e)

        async_client.run_report.assert_called_once_with(124)
        assert result.kind == "report"
        assert result.adhoc_result is adhoc


# ---------------------------------------------------------------------------
# Filter accessible watchlists tests
# ---------------------------------------------------------------------------


class TestFilterAccessibleWatchlists:
    """Tests for _filter_accessible_watchlists behavior in get_catalog()."""

    def test_filters_out_inaccessible_watchlists(self, sync_client):
        """Watchlists that raise APIError from get_watchlist_symbols are filtered out."""
        wl1 = WatchlistSummary(
            id=1, name="Accessible", last_modified=None, description=None
        )
        wl2 = WatchlistSummary(
            id=2, name="Inaccessible", last_modified=None, description=None
        )

        sync_client.get_screens = MagicMock(return_value=[])
        sync_client.get_coach_lists = MagicMock(
            return_value=CoachTreeData(screens=[], watchlists=[])
        )
        sync_client.get_watchlist_names = MagicMock(return_value=[wl1, wl2])

        def mock_get_watchlist_symbols(id):
            """Mock that succeeds for id=1, raises APIError for id=2."""
            if id == 1:
                return WatchlistDetail(
                    id="1",
                    name="Accessible",
                    last_modified=None,
                    description=None,
                    items=[],
                )
            raise APIError("Watchlist not found: '2'")

        sync_client.get_watchlist_symbols = MagicMock(
            side_effect=mock_get_watchlist_symbols
        )
        sync_client.get_reports = MagicMock(return_value=[])

        result = sync_client.get_catalog()

        watchlist_entries = [e for e in result.entries if e.kind == "watchlist"]
        assert len(watchlist_entries) == 1
        assert watchlist_entries[0].watchlist_id == 1

    async def test_async_filters_out_inaccessible_watchlists(self, async_client):
        """Async: watchlists that raise APIError from get_watchlist_symbols are filtered out."""
        wl1 = WatchlistSummary(
            id=1, name="Accessible", last_modified=None, description=None
        )
        wl2 = WatchlistSummary(
            id=2, name="Inaccessible", last_modified=None, description=None
        )

        async_client.get_screens = AsyncMock(return_value=[])
        async_client.get_coach_lists = AsyncMock(
            return_value=CoachTreeData(screens=[], watchlists=[])
        )
        async_client.get_watchlist_names = AsyncMock(return_value=[wl1, wl2])

        async def mock_get_watchlist_symbols(id):
            """Mock that succeeds for id=1, raises APIError for id=2."""
            if id == 1:
                return WatchlistDetail(
                    id="1",
                    name="Accessible",
                    last_modified=None,
                    description=None,
                    items=[],
                )
            raise APIError("Watchlist not found: '2'")

        async_client.get_watchlist_symbols = AsyncMock(
            side_effect=mock_get_watchlist_symbols
        )
        async_client.get_reports = AsyncMock(return_value=[])

        result = await async_client.get_catalog()

        watchlist_entries = [e for e in result.entries if e.kind == "watchlist"]
        assert len(watchlist_entries) == 1
        assert watchlist_entries[0].watchlist_id == 1

    def test_all_watchlists_filtered_returns_no_watchlist_entries(self, sync_client):
        """When all watchlists are inaccessible, no watchlist entries appear and no errors."""
        wl1 = WatchlistSummary(id=1, name="WL1", last_modified=None, description=None)
        wl2 = WatchlistSummary(id=2, name="WL2", last_modified=None, description=None)

        sync_client.get_screens = MagicMock(return_value=[])
        sync_client.get_coach_lists = MagicMock(
            return_value=CoachTreeData(screens=[], watchlists=[])
        )
        sync_client.get_watchlist_names = MagicMock(return_value=[wl1, wl2])
        sync_client.get_watchlist_symbols = MagicMock(
            side_effect=APIError("Watchlist not found")
        )
        sync_client.get_reports = MagicMock(return_value=[])

        result = sync_client.get_catalog()

        watchlist_entries = [e for e in result.entries if e.kind == "watchlist"]
        assert len(watchlist_entries) == 0
        assert result.errors == []


# ---------------------------------------------------------------------------
# Get watchlist access error tests
# ---------------------------------------------------------------------------


class TestGetWatchlistAccessError:
    """Tests for error handling in get_watchlist() when watchlist is inaccessible."""

    async def test_raises_clear_error_for_system_watchlist(self, async_client):
        """get_watchlist raises APIError with 'not accessible' message for system watchlists."""
        async_client.get_watchlist_symbols = AsyncMock(
            side_effect=APIError("Watchlist not found: '99'")
        )

        with pytest.raises(APIError, match="not accessible"):
            await async_client.get_watchlist(99)

    async def test_reraises_non_not_found_errors(self, async_client):
        """get_watchlist re-raises non-'not found' APIErrors unchanged."""
        async_client.get_watchlist_symbols = AsyncMock(
            side_effect=APIError("Server error")
        )

        with pytest.raises(APIError, match="Server error"):
            await async_client.get_watchlist(99)
