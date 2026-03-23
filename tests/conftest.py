"""Pytest configuration and shared fixtures for MarketSurge tests."""

import json
import pathlib

import pytest

FIXTURES_DIR = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def stock_response():
    """Load the stock response fixture from JSON."""
    with open(FIXTURES_DIR / "stock_response.json") as f:
        return json.load(f)


@pytest.fixture
def stock_extracted():
    """Load the stock extracted fixture from JSON."""
    with open(FIXTURES_DIR / "stock_extracted.json") as f:
        return json.load(f)


@pytest.fixture
def watchlist_names_response():
    """Load the watchlist names response fixture from JSON."""
    with open(FIXTURES_DIR / "watchlist_names_response.json") as f:
        return json.load(f)


@pytest.fixture
def flagged_symbols_response():
    """Load the flagged symbols response fixture from JSON."""
    with open(FIXTURES_DIR / "flagged_symbols_response.json") as f:
        return json.load(f)


@pytest.fixture
def screens_response():
    """Load the screens response fixture from JSON."""
    with open(FIXTURES_DIR / "screens_response.json") as f:
        return json.load(f)


@pytest.fixture
def screen_result_response():
    """Load the screen result response fixture from JSON."""
    with open(FIXTURES_DIR / "screen_result_response.json") as f:
        return json.load(f)


@pytest.fixture
def chart_data_response():
    """Load the chart data response fixture from JSON."""
    with open(FIXTURES_DIR / "chart_data_response.json") as f:
        return json.load(f)


@pytest.fixture
def fundamentals_response():
    """Load the fundamentals response fixture from JSON."""
    with open(FIXTURES_DIR / "fundamentals_response.json") as f:
        return json.load(f)


@pytest.fixture
def active_alerts_response():
    """Load the active alerts response fixture from JSON."""
    with open(FIXTURES_DIR / "active_alerts_response.json") as f:
        return json.load(f)


@pytest.fixture
def triggered_alerts_response():
    """Load the triggered alerts response fixture from JSON."""
    with open(FIXTURES_DIR / "triggered_alerts_response.json") as f:
        return json.load(f)


@pytest.fixture
def layouts_response():
    """Load the layouts response fixture from JSON."""
    with open(FIXTURES_DIR / "layouts_response.json") as f:
        return json.load(f)


@pytest.fixture
def chart_markups_response():
    """Load the chart markups response fixture from JSON."""
    with open(FIXTURES_DIR / "chart_markups_response.json") as f:
        return json.load(f)
