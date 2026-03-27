"""Serialization base class for TickerScope dataclass models."""

from __future__ import annotations

import dataclasses
import json
import logging
import types
import typing
from typing import Any, Self

_log = logging.getLogger("tickerscope")


class SerializableDataclass:
    """Base class for dict and JSON serialization helpers."""

    __slots__ = ()

    def to_dict(
        self,
        *,
        omit_none: bool = True,
        fields: set[str] | None = None,
    ) -> dict[str, Any]:
        """Convert this dataclass instance to a dictionary.

        Args:
            omit_none: Skip top-level dataclass fields with ``None`` values when true.
            fields: When provided, only include these field names in the output.
                Fields not present on the dataclass are silently ignored.
                The filter applies recursively to nested ``SerializableDataclass``
                instances and lists of them.

        Returns:
            Serialized dictionary for this dataclass.
        """
        result: dict[str, Any] = {}
        for field in dataclasses.fields(self):  # type: ignore
            if fields is not None and field.name not in fields:
                continue
            value = getattr(self, field.name)
            if value is None and omit_none:
                continue
            result[field.name] = self._convert_value(
                value, omit_none=omit_none, fields=fields
            )
        return result

    def _convert_value(
        self,
        value: Any,
        *,
        omit_none: bool,
        fields: set[str] | None = None,
    ) -> Any:
        """Recursively convert nested dataclasses for dict serialization.

        Args:
            value: Raw field value to convert.
            omit_none: Omit top-level ``None`` values in nested dataclasses.
            fields: When provided, only include these field names in nested
                dataclass output.

        Returns:
            Converted value suitable for JSON-serializable dict output.
        """
        if isinstance(value, SerializableDataclass):
            return value.to_dict(omit_none=omit_none, fields=fields)

        if isinstance(value, list):
            return [
                item.to_dict(omit_none=omit_none, fields=fields)
                if isinstance(item, SerializableDataclass)
                else item
                for item in value
            ]

        return value

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Construct a dataclass instance from a dictionary.

        Args:
            data: Mapping of field names to raw values.

        Returns:
            Constructed dataclass instance.
        """
        hints = typing.get_type_hints(cls)
        kwargs: dict[str, Any] = {}
        for field in dataclasses.fields(typing.cast(Any, cls)):
            if field.name not in data:
                continue
            raw_value = data[field.name]
            hint = hints.get(field.name, Any)
            kwargs[field.name] = cls._coerce_field(raw_value, hint)
        return cls(**kwargs)

    @classmethod
    def _coerce_field(cls, value: Any, hint: Any) -> Any:
        """Coerce nested dataclass values based on field type hints.

        Args:
            value: Raw value from input data.
            hint: Resolved field type hint.

        Returns:
            Coerced value for dataclass construction.
        """
        if value is None:
            return None

        origin = typing.get_origin(hint)

        if origin in (typing.Union, types.UnionType):
            return cls._coerce_union(value, typing.get_args(hint))

        if origin is list and isinstance(value, list):
            return cls._coerce_list(value, typing.get_args(hint))

        if cls._is_serializable_type(hint) and isinstance(value, dict):
            return hint.from_dict(value)

        return value

    @classmethod
    def _coerce_union(cls, value: Any, args: tuple[Any, ...]) -> Any:
        """Coerce values for ``Union`` field annotations.

        Args:
            value: Raw value from input data.
            args: Candidate union member types.

        Returns:
            Coerced value for first matching member, otherwise original value.
        """
        for arg in args:
            if arg is type(None):
                continue
            if cls._is_serializable_type(arg) and isinstance(value, dict):
                return arg.from_dict(value)
            if typing.get_origin(arg) is list:
                return cls._coerce_field(value, arg)
        return value

    @classmethod
    def _coerce_list(cls, value: list[Any], args: tuple[Any, ...]) -> Any:
        """Coerce values for ``list[T]`` field annotations.

        Args:
            value: Raw list value from input data.
            args: Generic type arguments for ``list[T]``.

        Returns:
            Coerced list where nested dataclass dicts are reconstructed.
        """
        if not args:
            return value

        item_hint = args[0]
        if not cls._is_serializable_type(item_hint):
            return value

        return [
            item_hint.from_dict(item) if isinstance(item, dict) else item
            for item in value
        ]

    @staticmethod
    def _is_serializable_type(value: Any) -> bool:
        """Return true when value is a SerializableDataclass class type."""
        return isinstance(value, type) and issubclass(value, SerializableDataclass)

    def to_json(
        self,
        *,
        omit_none: bool = True,
        fields: set[str] | None = None,
    ) -> str:
        """Serialize this dataclass instance to JSON.

        Args:
            omit_none: Skip top-level dataclass fields with ``None`` values when true.
            fields: When provided, only include these field names in the output.

        Returns:
            JSON string for this dataclass.
        """
        return json.dumps(self.to_dict(omit_none=omit_none, fields=fields))
