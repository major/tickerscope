"""Tests for SerializableDataclass base serialization behavior."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, dataclass
from typing import Any

import pytest

from tickerscope._serialization import SerializableDataclass  # pyright: ignore[reportMissingImports]


@dataclass(frozen=True, slots=True)
class FlatModel(SerializableDataclass):
    """Flat model used for basic to_dict/to_json/from_dict checks."""

    name: str | None
    value: int | None


@dataclass(frozen=True, slots=True)
class ChildModel(SerializableDataclass):
    """Nested child model for omit_none propagation and from_dict tests."""

    child_name: str | None
    child_value: int | None


@dataclass(frozen=True, slots=True)
class ParentModel(SerializableDataclass):
    """Parent model containing a nested child model."""

    parent_name: str | None
    child: ChildModel | None


@dataclass(frozen=True, slots=True)
class OpaquePayloadModel(SerializableDataclass):
    """Model with opaque dict payload that must pass through unchanged."""

    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class ListWithOptionalValuesModel(SerializableDataclass):
    """Model with list[str | None] that preserves None list entries."""

    dates: list[str | None]


@dataclass(frozen=True, slots=True)
class ListOfDictsModel(SerializableDataclass):
    """Model with list of dicts that preserves None values inside dicts."""

    rows: list[dict[str, str | None]]


@dataclass(frozen=True, slots=True)
class PropertyModel(SerializableDataclass):
    """Model with computed property that should not be serialized as a field."""

    value: int

    @property
    def doubled(self) -> int:
        """Return double of value."""
        return self.value * 2


@dataclass(frozen=True, slots=True)
class ChildCollectionModel(SerializableDataclass):
    """Model containing a list of nested dataclass children."""

    children: list[ChildModel]


def test_to_dict_default_omits_none() -> None:
    """Flat model to_dict() omits top-level None fields by default."""
    model = FlatModel(name="test", value=None)

    result = model.to_dict()

    assert result == {"name": "test"}


def test_to_dict_omit_none_false_includes_none() -> None:
    """Flat model to_dict(omit_none=False) keeps top-level None fields."""
    model = FlatModel(name="test", value=None)

    result = model.to_dict(omit_none=False)

    assert result == {"name": "test", "value": None}


def test_to_json_returns_valid_json_string() -> None:
    """Flat model to_json() returns a valid JSON string payload."""
    model = FlatModel(name="test", value=None)

    payload = model.to_json(omit_none=False)
    parsed = json.loads(payload)

    assert isinstance(payload, str)
    assert parsed == {"name": "test", "value": None}


def test_nested_to_dict_default_omits_none_in_child() -> None:
    """Nested parent to_dict() omits None fields inside child by default."""
    parent = ParentModel(
        parent_name="parent",
        child=ChildModel(child_name="child", child_value=None),
    )

    result = parent.to_dict()

    assert result == {
        "parent_name": "parent",
        "child": {"child_name": "child"},
    }


def test_nested_to_dict_omit_none_false_includes_none_in_child() -> None:
    """Nested parent to_dict(omit_none=False) includes None fields in child."""
    parent = ParentModel(
        parent_name="parent",
        child=ChildModel(child_name="child", child_value=None),
    )

    result = parent.to_dict(omit_none=False)

    assert result == {
        "parent_name": "parent",
        "child": {"child_name": "child", "child_value": None},
    }


def test_opaque_dict_passthrough_preserves_none_values() -> None:
    """Opaque dict payload preserves inner None values with omit_none enabled."""
    payload = {"key": None, "nested": {"a": 1}}
    model = OpaquePayloadModel(payload=payload)

    result = model.to_dict()

    assert result == {"payload": payload}


def test_list_of_optional_values_preserves_none_entries() -> None:
    """list[str | None] preserves None elements when omit_none is enabled."""
    dates = ["2024-01-01", None, "2024-01-03"]
    model = ListWithOptionalValuesModel(dates=dates)

    result = model.to_dict()

    assert result == {"dates": dates}


def test_list_of_dicts_preserves_none_values_inside_dicts() -> None:
    """list[dict[str, str | None]] preserves dict-internal None values."""
    rows = [{"ticker": "AAPL", "price": None}]
    model = ListOfDictsModel(rows=rows)

    result = model.to_dict()

    assert result == {"rows": rows}


def test_property_not_in_to_dict_output() -> None:
    """Properties are excluded because serialization only uses dataclass fields."""
    model = PropertyModel(value=21)

    result = model.to_dict()

    assert result == {"value": 21}
    assert "doubled" not in result


def test_from_dict_round_trip_flat_model() -> None:
    """Flat model from_dict() round-trips dict values correctly."""
    data = {"name": "test", "value": 7}

    model = FlatModel.from_dict(data)

    assert model == FlatModel(name="test", value=7)
    assert model.to_dict(omit_none=False) == data


def test_from_dict_nested_model() -> None:
    """Nested dataclass fields are recursively constructed from dict inputs."""
    data = {
        "parent_name": "parent",
        "child": {"child_name": "child", "child_value": 5},
    }

    model = ParentModel.from_dict(data)

    assert model == ParentModel(
        parent_name="parent",
        child=ChildModel(child_name="child", child_value=5),
    )


def test_from_dict_list_of_dataclasses() -> None:
    """from_dict() maps over list items for list[SomeDataclass] fields."""
    data = {
        "children": [
            {"child_name": "one", "child_value": 1},
            {"child_name": "two", "child_value": None},
        ]
    }

    model = ChildCollectionModel.from_dict(data)

    assert model == ChildCollectionModel(
        children=[
            ChildModel(child_name="one", child_value=1),
            ChildModel(child_name="two", child_value=None),
        ]
    )


def test_frozen_dataclass_enforcement() -> None:
    """Frozen dataclass model rejects attribute assignment."""
    model = FlatModel(name="immutable", value=1)

    with pytest.raises(FrozenInstanceError):
        model.name = "mutated"  # type: ignore[misc]
