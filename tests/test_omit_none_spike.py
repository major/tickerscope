"""Spike test for mashumaro TO_DICT_ADD_OMIT_NONE_FLAG with frozen+slots dataclasses.

Validates that:
1. TO_DICT_ADD_OMIT_NONE_FLAG can be imported from mashumaro.config
2. Backward compat: model.to_dict() (no args) omits None fields
3. New behavior: model.to_dict(omit_none=False) includes None fields as explicit nulls
4. Nested propagation: parent.to_dict(omit_none=False) includes nulls in nested child
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from mashumaro.config import BaseConfig  # pyright: ignore[reportMissingImports]
from mashumaro.config import TO_DICT_ADD_OMIT_NONE_FLAG  # pyright: ignore[reportMissingImports]
from mashumaro.mixins.dict import DataClassDictMixin  # pyright: ignore[reportMissingImports]


# ---------------------------------------------------------------------------
# Test 1: Flag is importable
# ---------------------------------------------------------------------------


def test_flag_importable() -> None:
    """Verify TO_DICT_ADD_OMIT_NONE_FLAG is importable and not None."""
    assert TO_DICT_ADD_OMIT_NONE_FLAG is not None


# ---------------------------------------------------------------------------
# Test 2: Backward compat - to_dict() with no args omits None
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FlatModel(DataClassDictMixin):
    """Minimal frozen+slots model with omit_none=True and flag enabled."""

    class Config(BaseConfig):
        omit_none = True
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]

    name: str | None
    value: int | None


def test_to_dict_default_omits_none() -> None:
    """Verify model.to_dict() with no args omits None fields (backward compat)."""
    model = FlatModel(name="test", value=None)
    result = model.to_dict()

    # Should omit the None value field
    assert "name" in result
    assert result["name"] == "test"
    assert "value" not in result


# ---------------------------------------------------------------------------
# Test 3: New behavior - to_dict(omit_none=False) includes None
# ---------------------------------------------------------------------------


def test_to_dict_omit_none_false_includes_none() -> None:
    """Verify model.to_dict(omit_none=False) includes None fields as explicit nulls."""
    model = FlatModel(name="test", value=None)
    result = model.to_dict(omit_none=False)

    # Should include the None value field as explicit null
    assert "name" in result
    assert result["name"] == "test"
    assert "value" in result
    assert result["value"] is None


# ---------------------------------------------------------------------------
# Test 4: to_json is tested in task 2 (placeholder)
# ---------------------------------------------------------------------------


def test_to_json_not_tested_here() -> None:
    """Note: to_json() serialization is tested in task 2, not here."""
    model = FlatModel(name="test", value=None)
    json_str = json.dumps(model.to_dict())
    assert isinstance(json_str, str)


# ---------------------------------------------------------------------------
# Test 5: Nested propagation - parent.to_dict(omit_none=False) includes nulls in child
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ChildModel(DataClassDictMixin):
    """Nested child model with omit_none=True and flag enabled."""

    class Config(BaseConfig):
        omit_none = True
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]

    child_name: str | None
    child_value: int | None


@dataclass(frozen=True, slots=True)
class ParentModel(DataClassDictMixin):
    """Parent model containing a nested child with omit_none=True and flag enabled."""

    class Config(BaseConfig):
        omit_none = True
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]

    parent_name: str | None
    child: ChildModel | None


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
