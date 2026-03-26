"""Tests for CoachTree query parsing and client methods."""

# pyright: reportMissingImports=false

from __future__ import annotations

import httpx
import pytest
import respx

from tickerscope._models import CoachTreeData, NavTreeFolder, NavTreeLeaf
from tickerscope._parsing import parse_coach_tree_response


def test_parse_coach_tree_response_returns_coach_tree_data(
    coach_tree_response,
) -> None:
    """Parse fixture into CoachTreeData with both watchlists and screens lists."""
    result = parse_coach_tree_response(coach_tree_response)

    assert isinstance(result, CoachTreeData)
    assert isinstance(result.watchlists, list)
    assert len(result.watchlists) == 2
    assert isinstance(result.screens, list)
    assert len(result.screens) == 3


def test_watchlists_contain_folder_and_leaf(coach_tree_response) -> None:
    """Watchlists list contains both NavTreeFolder and NavTreeLeaf instances."""
    result = parse_coach_tree_response(coach_tree_response)

    folders = [n for n in result.watchlists if isinstance(n, NavTreeFolder)]
    leaves = [n for n in result.watchlists if isinstance(n, NavTreeLeaf)]
    assert len(folders) == 1
    assert len(leaves) == 1
    assert folders[0].name == "IBD Live Watch"
    assert leaves[0].name == "S&P 500"


def test_screens_contain_folder_and_leaves(coach_tree_response) -> None:
    """Screens list contains folders and coach screen leaves."""
    result = parse_coach_tree_response(coach_tree_response)

    folders = [n for n in result.screens if isinstance(n, NavTreeFolder)]
    leaves = [n for n in result.screens if isinstance(n, NavTreeLeaf)]
    assert len(folders) == 1
    assert folders[0].name == "MarketSurge Stock Screens"
    assert len(folders[0].children) == 1
    assert len(leaves) == 2
    assert leaves[0].name == "William J. O'Neil"


def test_coach_leaf_dual_reference_ids(coach_tree_response) -> None:
    """Coach leaf with both watchlistId and screenId in referenceId populates both fields."""
    result = parse_coach_tree_response(coach_tree_response)
    leaf = next(
        n
        for n in result.watchlists
        if isinstance(n, NavTreeLeaf) and n.name == "S&P 500"
    )

    assert leaf.reference_watchlist_id == "94490110509978"
    assert leaf.reference_screen_id == "01KF1ENSYEXKTCXPWKPRQ4S92N"


def test_empty_coach_trees() -> None:
    """Empty watchlists and screens return CoachTreeData with empty lists."""
    raw = {"data": {"user": {"watchlists": [], "screens": []}}}
    result = parse_coach_tree_response(raw)

    assert isinstance(result, CoachTreeData)
    assert result.watchlists == []
    assert result.screens == []


@respx.mock
def test_sync_client_get_coach_lists(sync_client, coach_tree_response) -> None:
    """Sync client get_coach_lists returns parsed CoachTreeData."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=coach_tree_response)
    )

    result = sync_client.get_coach_lists()

    assert isinstance(result, CoachTreeData)
    assert len(result.watchlists) == 2
    assert len(result.screens) == 3


@pytest.mark.asyncio
@respx.mock
async def test_async_client_get_coach_lists(async_client, coach_tree_response) -> None:
    """Async client get_coach_lists returns parsed CoachTreeData."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=coach_tree_response)
    )

    result = await async_client.get_coach_lists()

    assert isinstance(result, CoachTreeData)
    assert len(result.watchlists) == 2
    assert len(result.screens) == 3
