"""Behavioral tests for SerializableDataclass omit_none flag.

Validates that:
1. Backward compat: model.to_dict() (no args) omits None fields
2. Explicit behavior: model.to_dict(omit_none=False) includes None fields as explicit nulls
3. Nested propagation: parent.to_dict(omit_none=False) includes nulls in nested child
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from tickerscope._serialization import SerializableDataclass  # pyright: ignore[reportMissingImports]


# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FlatModel(SerializableDataclass):
    """Minimal frozen+slots model for omit_none testing."""

    name: str | None
    value: int | None


@dataclass(frozen=True, slots=True)
class ChildModel(SerializableDataclass):
    """Nested child model for propagation testing."""

    child_name: str | None
    child_value: int | None


@dataclass(frozen=True, slots=True)
class ParentModel(SerializableDataclass):
    """Parent model containing a nested child."""

    parent_name: str | None
    child: ChildModel | None


# ---------------------------------------------------------------------------
# Test 1: Backward compat - to_dict() with no args omits None
# ---------------------------------------------------------------------------


def test_to_dict_default_omits_none() -> None:
    """Verify model.to_dict() with no args omits None fields (backward compat)."""
    model = FlatModel(name="test", value=None)
    result = model.to_dict()

    assert "name" in result
    assert result["name"] == "test"
    assert "value" not in result


# ---------------------------------------------------------------------------
# Test 2: New behavior - to_dict(omit_none=False) includes None
# ---------------------------------------------------------------------------


def test_to_dict_omit_none_false_includes_none() -> None:
    """Verify model.to_dict(omit_none=False) includes None fields as explicit nulls."""
    model = FlatModel(name="test", value=None)
    result = model.to_dict(omit_none=False)

    assert "name" in result
    assert result["name"] == "test"
    assert "value" in result
    assert result["value"] is None


# ---------------------------------------------------------------------------
# Test 3: to_json roundtrip via json.dumps
# ---------------------------------------------------------------------------


def test_to_json_not_tested_here() -> None:
    """Note: to_json() is tested in test_serialization.py; this is a sanity check."""
    model = FlatModel(name="test", value=None)
    json_str = json.dumps(model.to_dict())
    assert isinstance(json_str, str)


# ---------------------------------------------------------------------------
# Test 4: Nested propagation
# ---------------------------------------------------------------------------


def test_nested_propagation() -> None:
    """Verify parent.to_dict(omit_none=False) includes nulls in nested child."""
    child = ChildModel(child_name="child_test", child_value=None)
    parent = ParentModel(parent_name="parent_test", child=child)

    # Default: omit None fields
    result_default = parent.to_dict()
    assert "parent_name" in result_default
    assert "child" in result_default
    assert "child_name" in result_default["child"]
    assert "child_value" not in result_default["child"]

    # With omit_none=False: include None fields in both parent and child
    result_with_nulls = parent.to_dict(omit_none=False)
    assert "parent_name" in result_with_nulls
    assert result_with_nulls["parent_name"] == "parent_test"
    assert "child" in result_with_nulls
    assert "child_name" in result_with_nulls["child"]
    assert result_with_nulls["child"]["child_name"] == "child_test"
    assert "child_value" in result_with_nulls["child"]
    assert result_with_nulls["child"]["child_value"] is None
