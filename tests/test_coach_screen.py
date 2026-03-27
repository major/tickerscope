"""Tests for RunScreen (coach account screen) parsing and client helpers."""

from __future__ import annotations

import pytest

from tickerscope._client import (
    BaseTickerScopeClient,
    _find_coach_screen,
    _list_coach_screen_names,
)
from tickerscope._exceptions import APIError
from tickerscope._models import NavTreeFolder, NavTreeLeaf, ScreenResult
from tickerscope._parsing import parse_coach_tree_response, parse_run_screen_response


def test_parse_run_screen_response(run_screen_response) -> None:
    """Parse fixture into ScreenResult with correct row data."""
    result = parse_run_screen_response(run_screen_response)

    assert isinstance(result, ScreenResult)
    assert result.num_instruments == 48
    assert result.screen_name is None
    assert result.elapsed_time is None
    assert len(result.rows) == 2
    assert result.rows[0]["Symbol"] == "PKE"
    assert result.rows[0]["CompanyName"] == "Park Aerospace Corp."
    assert result.rows[1]["Symbol"] == "AAUC"


def test_parse_run_screen_empty() -> None:
    """Return ScreenResult with empty rows when responseValues is empty."""
    raw = {
        "data": {
            "user": {
                "runScreen": {
                    "numberOfMatchingInstruments": 0,
                    "responseValues": [],
                }
            }
        }
    }
    result = parse_run_screen_response(raw)

    assert result.rows == []
    assert result.num_instruments == 0


def test_parse_run_screen_null_data() -> None:
    """Raise APIError when user.runScreen is null."""
    with pytest.raises(APIError, match="No coach screen data"):
        parse_run_screen_response({"data": {"user": {"runScreen": None}}})


def test_parse_run_screen_missing_user() -> None:
    """Raise APIError when user key is missing entirely."""
    with pytest.raises(APIError, match="No coach screen data"):
        parse_run_screen_response({"data": {}})


def _make_leaf(name: str, node_type: str, screen_id: str | None = None) -> NavTreeLeaf:
    """Build a minimal NavTreeLeaf for testing."""
    return NavTreeLeaf(
        id="test-id",
        name=name,
        parent_id=None,
        node_type=node_type,
        tree_type="MSR_NAV",
        url=None,
        reference_id=None,
        reference_watchlist_id=None,
        reference_screen_id=screen_id,
    )


def _make_folder(name: str, children: list) -> NavTreeFolder:
    """Build a minimal NavTreeFolder for testing."""
    return NavTreeFolder(
        id="folder-id",
        name=name,
        parent_id=None,
        node_type="SYSTEM_FOLDER",
        tree_type="MSR_NAV",
        children=children,
        content_type="STOCK_SCREEN",
    )


class TestFindCoachScreen:
    """Tests for _find_coach_screen helper."""

    def test_finds_top_level_screen(self) -> None:
        """Find a screen at the top level of the tree."""
        leaf = _make_leaf("William J. O'Neil", "STOCK_SCREEN", "abc123")
        result = _find_coach_screen([leaf], "William J. O'Neil")

        assert result is leaf

    def test_finds_nested_screen(self) -> None:
        """Find a screen nested inside a folder."""
        leaf = _make_leaf("Warren Buffett", "STOCK_SCREEN", "def456")
        folder = _make_folder("MarketSurge Stock Screens", [leaf])
        result = _find_coach_screen([folder], "Warren Buffett")

        assert result is leaf

    def test_returns_none_for_no_match(self) -> None:
        """Return None when no screen matches."""
        leaf = _make_leaf("Peter Lynch", "STOCK_SCREEN", "ghi789")
        result = _find_coach_screen([leaf], "NonExistent")

        assert result is None

    def test_skips_folders(self) -> None:
        """Skip folder nodes that happen to share the name."""
        folder = _make_folder("William J. O'Neil", [])
        result = _find_coach_screen([folder], "William J. O'Neil")

        assert result is None

    def test_skips_non_screen_types(self) -> None:
        """Skip leaves that aren't STOCK_SCREEN or FUND_SCREEN."""
        leaf = _make_leaf("Watchlist Thing", "WATCHLIST", "xyz")
        result = _find_coach_screen([leaf], "Watchlist Thing")

        assert result is None

    def test_finds_fund_screen(self) -> None:
        """Find FUND_SCREEN type leaves."""
        leaf = _make_leaf("Top Rated Growth Funds", "FUND_SCREEN", "fund1")
        result = _find_coach_screen([leaf], "Top Rated Growth Funds")

        assert result is leaf


class TestListCoachScreenNames:
    """Tests for _list_coach_screen_names helper."""

    def test_collects_names(self) -> None:
        """Collect and sort screen names from the tree."""
        nodes = [
            _make_leaf("Zebra Screen", "STOCK_SCREEN"),
            _make_leaf("Alpha Screen", "STOCK_SCREEN"),
        ]
        result = _list_coach_screen_names(nodes)

        assert result == "Alpha Screen, Zebra Screen"

    def test_deduplicates(self) -> None:
        """Deduplicate screen names that appear in multiple places."""
        leaf = _make_leaf("IBD 50", "STOCK_SCREEN")
        folder = _make_folder("Folder", [leaf])
        result = _list_coach_screen_names([leaf, folder])

        assert result == "IBD 50"

    def test_empty_tree(self) -> None:
        """Return empty string for empty tree."""
        assert _list_coach_screen_names([]) == ""


def test_find_coach_screen_in_real_fixture(coach_tree_response) -> None:
    """Find 'William J. O'Neil' in the parsed coach tree fixture."""
    coach_data = parse_coach_tree_response(coach_tree_response)
    leaf = _find_coach_screen(coach_data.screens, "William J. O'Neil")

    assert leaf is not None
    assert leaf.name == "William J. O'Neil"
    assert leaf.reference_screen_id == "01KEFPH03H88ANE7DVPA15N4NS"


class TestCoachScreenPayload:
    """Tests for _build_run_coach_screen_payload static method."""

    def test_includes_empty_include_source(self) -> None:
        """Payload includes empty includeSource required by the ScreenResultInput schema."""
        payload = BaseTickerScopeClient._build_run_coach_screen_payload("abc123")
        assert payload["variables"]["input"]["includeSource"] == {}

    def test_sets_coach_account_true(self) -> None:
        """Payload sets coachAccount to True for coach screen dispatch."""
        payload = BaseTickerScopeClient._build_run_coach_screen_payload("abc123")
        assert payload["variables"]["input"]["coachAccount"] is True

    def test_passes_screen_id(self) -> None:
        """Payload passes the screen ID through to the input."""
        payload = BaseTickerScopeClient._build_run_coach_screen_payload("xyz789")
        assert payload["variables"]["input"]["screenId"] == "xyz789"
