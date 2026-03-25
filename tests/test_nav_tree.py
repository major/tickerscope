"""Tests for NavTree query parsing and client methods."""

# pyright: reportMissingImports=false

from dataclasses import FrozenInstanceError

import httpx
import pytest
import respx

from tickerscope._models import NavTreeFolder, NavTreeLeaf
from tickerscope._parsing import _build_nav_tree_node, parse_nav_tree_response


def test_parse_nav_tree_response_types(nav_tree_response) -> None:
    """Parse fixture into list with correct NavTreeFolder and NavTreeLeaf types."""
    result = parse_nav_tree_response(nav_tree_response)

    assert isinstance(result, list)
    assert len(result) == 4

    folders = [n for n in result if isinstance(n, NavTreeFolder)]
    leaves = [n for n in result if isinstance(n, NavTreeLeaf)]
    assert len(folders) == 2
    assert len(leaves) == 2


def test_folder_has_children(nav_tree_response) -> None:
    """NavTreeFolder children are correctly parsed as NavTreeNode subtypes."""
    result = parse_nav_tree_response(nav_tree_response)
    folder = next(
        n for n in result if isinstance(n, NavTreeFolder) and n.name == "My Lists"
    )

    assert isinstance(folder.children, list)
    assert len(folder.children) == 2
    child_names = {c.name for c in folder.children}
    assert "My Watchlist" in child_names
    assert "My Screen" in child_names


def test_leaf_watchlist_reference_id(nav_tree_response) -> None:
    """NavTreeLeaf with watchlistId referenceId populates reference_watchlist_id."""
    result = parse_nav_tree_response(nav_tree_response)
    leaf = next(
        n for n in result if isinstance(n, NavTreeLeaf) and n.name == "Recent Symbols"
    )

    assert leaf.reference_watchlist_id == "266152633632307"
    assert leaf.reference_screen_id is None
    assert leaf.reference_id == '{"watchlistId": "266152633632307"}'


def test_leaf_screen_reference_id(nav_tree_response) -> None:
    """NavTreeLeaf with screenId referenceId populates reference_screen_id."""
    result = parse_nav_tree_response(nav_tree_response)
    leaf = next(
        n
        for n in result
        if isinstance(n, NavTreeLeaf) and n.node_type == "STOCK_SCREEN"
    )

    assert leaf.reference_screen_id == "01KJX696Z94RQPXK3EEH62GYNZ"
    assert leaf.reference_watchlist_id is None


def test_malformed_reference_id() -> None:
    """Malformed referenceId sets both reference fields to None without raising."""
    raw = {
        "id": "1",
        "name": "Bad",
        "parentId": None,
        "type": "WATCHLIST",
        "url": None,
        "treeType": "MSR_NAV",
        "referenceId": "not-json",
    }
    node = _build_nav_tree_node(raw)

    assert isinstance(node, NavTreeLeaf)
    assert node.reference_watchlist_id is None
    assert node.reference_screen_id is None
    assert node.reference_id == "not-json"


def test_empty_nav_tree() -> None:
    """Empty navTree returns empty list."""
    result = parse_nav_tree_response({"data": {"user": {"navTree": []}}})

    assert result == []


def test_empty_folder_children(nav_tree_response) -> None:
    """Folder with empty children list parses correctly."""
    result = parse_nav_tree_response(nav_tree_response)
    empty_folder = next(
        n for n in result if isinstance(n, NavTreeFolder) and n.name == "Empty Folder"
    )

    assert empty_folder.children == []
    assert empty_folder.content_type is None


@respx.mock
def test_sync_client_get_nav_tree(sync_client, nav_tree_response) -> None:
    """Sync client get_nav_tree returns parsed node list."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=nav_tree_response)
    )

    result = sync_client.get_nav_tree()

    assert isinstance(result, list)
    assert len(result) == 4
    assert isinstance(result[0], NavTreeFolder)


@pytest.mark.asyncio
@respx.mock
async def test_async_client_get_nav_tree(async_client, nav_tree_response) -> None:
    """Async client get_nav_tree returns parsed node list."""
    respx.post("https://shared-data.dowjones.io/gateway/graphql").mock(
        return_value=httpx.Response(200, json=nav_tree_response)
    )

    result = await async_client.get_nav_tree()

    assert isinstance(result, list)
    assert len(result) == 4
    assert isinstance(result[0], NavTreeFolder)


def test_nav_tree_node_frozen() -> None:
    """NavTreeNode hierarchy is immutable (frozen dataclass)."""
    leaf = NavTreeLeaf(
        id="1",
        name="Test",
        parent_id=None,
        node_type="WATCHLIST",
        tree_type="MSR_NAV",
        url=None,
        reference_id=None,
        reference_watchlist_id=None,
        reference_screen_id=None,
    )

    with pytest.raises(FrozenInstanceError):
        leaf.name = "changed"  # type: ignore[misc]


def test_nav_tree_folder_fields() -> None:
    """NavTreeFolder common fields are correctly populated by dispatcher."""
    raw = {
        "id": "f-1",
        "name": "Folder",
        "parentId": "root",
        "type": "SYSTEM_FOLDER",
        "children": [],
        "contentType": "WATCHLIST",
        "treeType": "MSR_NAV",
    }
    node = _build_nav_tree_node(raw)

    assert isinstance(node, NavTreeFolder)
    assert node.id == "f-1"
    assert node.parent_id == "root"
    assert node.node_type == "SYSTEM_FOLDER"
    assert node.content_type == "WATCHLIST"
    assert node.tree_type == "MSR_NAV"
