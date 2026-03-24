"""Tests for the capabilities() classmethod on BaseTickerScopeClient."""

from __future__ import annotations

import json

import pytest

from tickerscope import AsyncTickerScopeClient, BaseTickerScopeClient, TickerScopeClient

REQUIRED_TOP_LEVEL_KEYS = {"methods", "auth_required", "api_endpoint"}
REQUIRED_METHOD_KEYS = {
    "name",
    "parameters",
    "return_type",
    "supports_limit",
}

KNOWN_METHODS = [
    "get_stock",
    "get_chart_data",
    "get_watchlist",
    "get_watchlist_names",
    "get_watchlist_items",
    "get_screens",
    "run_screen",
    "get_fundamentals",
    "get_active_alerts",
    "get_triggered_alerts",
    "get_layouts",
    "get_chart_markups",
    "get_ownership",
]


class TestCapabilitiesStructure:
    """Verify the shape and contents of the capabilities dict."""

    @pytest.fixture()
    def caps(self) -> dict:
        """Return capabilities dict from the base class."""
        return BaseTickerScopeClient.capabilities()

    def test_returns_dict(self, caps: dict) -> None:
        """capabilities() returns a plain dict."""
        assert isinstance(caps, dict)

    def test_top_level_keys_present(self, caps: dict) -> None:
        """Dict contains methods, auth_required, and api_endpoint."""
        assert REQUIRED_TOP_LEVEL_KEYS.issubset(caps.keys())

    def test_auth_required_is_bool(self, caps: dict) -> None:
        """auth_required is a boolean."""
        assert isinstance(caps["auth_required"], bool)

    def test_api_endpoint_is_str(self, caps: dict) -> None:
        """api_endpoint is a non-empty string."""
        assert isinstance(caps["api_endpoint"], str)
        assert len(caps["api_endpoint"]) > 0

    def test_methods_is_list(self, caps: dict) -> None:
        """methods value is a list."""
        assert isinstance(caps["methods"], list)

    def test_methods_count(self, caps: dict) -> None:
        """At least 15 methods are advertised."""
        assert len(caps["methods"]) >= 15

    def test_each_method_has_required_keys(self, caps: dict) -> None:
        """Every method dict contains name, parameters, return_type, and supports_limit."""
        for method in caps["methods"]:
            missing = REQUIRED_METHOD_KEYS - method.keys()
            assert not missing, (
                f"Method {method.get('name', '???')} missing keys: {missing}"
            )

    def test_method_name_is_str(self, caps: dict) -> None:
        """Every method name is a non-empty string."""
        for method in caps["methods"]:
            assert isinstance(method["name"], str)
            assert len(method["name"]) > 0

    def test_supports_limit_is_bool(self, caps: dict) -> None:
        """supports_limit is a boolean for every method."""
        for method in caps["methods"]:
            assert isinstance(method["supports_limit"], bool), (
                f"{method['name']}: supports_limit is {type(method['supports_limit'])}"
            )

    def test_return_type_is_str(self, caps: dict) -> None:
        """return_type is a non-empty string for every method."""
        for method in caps["methods"]:
            assert isinstance(method["return_type"], str)
            assert len(method["return_type"]) > 0

    def test_parameters_is_list(self, caps: dict) -> None:
        """parameters is a list for every method."""
        for method in caps["methods"]:
            assert isinstance(method["parameters"], list), (
                f"{method['name']}: parameters is {type(method['parameters'])}"
            )


class TestCapabilitiesKnownMethods:
    """Verify that specific well-known methods are present."""

    @pytest.fixture()
    def method_names(self) -> set[str]:
        """Return the set of method names from capabilities."""
        caps = BaseTickerScopeClient.capabilities()
        return {m["name"] for m in caps["methods"]}

    @pytest.mark.parametrize("name", KNOWN_METHODS)
    def test_known_method_present(self, method_names: set[str], name: str) -> None:
        """Each known public API method appears in capabilities."""
        assert name in method_names


class TestCapabilitiesSerializable:
    """Verify the capabilities dict is JSON-serializable."""

    def test_json_dumps_succeeds(self) -> None:
        """json.dumps(capabilities()) produces valid JSON without raising."""
        caps = BaseTickerScopeClient.capabilities()
        result = json.dumps(caps)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_roundtrip(self) -> None:
        """JSON encode-then-decode preserves the dict structure."""
        caps = BaseTickerScopeClient.capabilities()
        roundtripped = json.loads(json.dumps(caps))
        assert roundtripped == caps


class TestCapabilitiesCallable:
    """Verify capabilities() works as a classmethod on all client classes."""

    @pytest.mark.parametrize(
        "cls",
        [BaseTickerScopeClient, TickerScopeClient, AsyncTickerScopeClient],
        ids=["base", "sync", "async"],
    )
    def test_callable_without_instantiation(self, cls: type) -> None:
        """capabilities() is callable on the class itself, no token needed."""
        caps = cls.capabilities()
        assert isinstance(caps, dict)
        assert "methods" in caps

    def test_sync_and_async_return_same_data(self) -> None:
        """Both client classes return identical capabilities."""
        assert TickerScopeClient.capabilities() == AsyncTickerScopeClient.capabilities()
