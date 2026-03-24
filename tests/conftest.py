"""Pytest configuration and shared fixtures for MarketSurge tests."""

import json
import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


def _json_fixture(filename: str):
    """Create a pytest fixture that loads a JSON file from the fixtures directory."""

    @pytest.fixture(name=filename.removesuffix(".json"))
    def _load():
        with open(FIXTURES_DIR / filename) as f:
            return json.load(f)

    return _load


stock_response = _json_fixture("stock_response.json")
stock_extracted = _json_fixture("stock_extracted.json")
watchlist_names_response = _json_fixture("watchlist_names_response.json")
flagged_symbols_response = _json_fixture("flagged_symbols_response.json")
screens_response = _json_fixture("screens_response.json")
screen_result_response = _json_fixture("screen_result_response.json")
chart_data_response = _json_fixture("chart_data_response.json")
fundamentals_response = _json_fixture("fundamentals_response.json")
active_alerts_response = _json_fixture("active_alerts_response.json")
triggered_alerts_response = _json_fixture("triggered_alerts_response.json")
layouts_response = _json_fixture("layouts_response.json")
chart_markups_response = _json_fixture("chart_markups_response.json")
