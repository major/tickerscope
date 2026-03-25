"""Tests for AllPanels query parsing and client methods."""

from dataclasses import FrozenInstanceError

import pytest

from tickerscope._models import Panel
from tickerscope._parsing import parse_panels_response


def test_parse_panels_response(panels_response) -> None:
    """Parse fixture into Panel list with correct fields."""
    result = parse_panels_response(panels_response)

    assert len(result) == 3
    assert result[0].id == "panel-uuid-1"
    assert result[0].name == "My Layout"
    assert result[0].site == "marketsurge"
    assert result[0].panel_type == "LAYOUT"
    assert isinstance(result[0].data, dict)
    assert result[0].data.get("symbol") == "AAPL"
    assert result[0].created_at == "2025-01-15T10:30:00.000Z"
    assert result[0].updated_at == "2025-03-20T14:22:00.000Z"


def test_parse_panels_empty() -> None:
    """Return empty list when panels array is empty."""
    result = parse_panels_response({"data": {"user": {"panels": []}}})

    assert result == []


def test_parse_panels_multiple_types(panels_response) -> None:
    """Parse panels with different types (LAYOUT, ALERTS_SETTING, APPLICATION_SETTINGS)."""
    result = parse_panels_response(panels_response)

    types = {p.panel_type for p in result}
    assert "LAYOUT" in types
    assert "ALERTS_SETTING" in types
    assert "APPLICATION_SETTINGS" in types


def test_parse_panels_data_passthrough(panels_response) -> None:
    """Panel.data is passed through as dict without parsing."""
    result = parse_panels_response(panels_response)

    layout = next(p for p in result if p.panel_type == "LAYOUT")
    assert isinstance(layout.data, dict)
    assert layout.data.get("chartType") == "hlc_box"
    assert layout.data.get("showEarnings") is True

    alerts = next(p for p in result if p.panel_type == "ALERTS_SETTING")
    assert isinstance(alerts.data, dict)
    assert alerts.data.get("alertThreshold") == 5


def test_panel_frozen() -> None:
    """Panel is immutable (frozen dataclass)."""
    panel = Panel(
        id="1",
        name="Test",
        site="marketsurge",
        panel_type="LAYOUT",
        data={"key": "value"},
        created_at=None,
        updated_at=None,
    )

    with pytest.raises(FrozenInstanceError):
        panel.name = "changed"  # type: ignore[misc]


def test_panel_created_at_dt(panels_response) -> None:
    """Panel.created_at_dt parses ISO datetime string."""
    result = parse_panels_response(panels_response)

    layout = result[0]
    assert layout.created_at_dt is not None
    assert layout.created_at_dt.year == 2025
    assert layout.created_at_dt.month == 1
    assert layout.created_at_dt.day == 15


def test_panel_updated_at_dt(panels_response) -> None:
    """Panel.updated_at_dt parses ISO datetime string."""
    result = parse_panels_response(panels_response)

    layout = result[0]
    assert layout.updated_at_dt is not None
    assert layout.updated_at_dt.year == 2025
    assert layout.updated_at_dt.month == 3
    assert layout.updated_at_dt.day == 20
