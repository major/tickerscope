"""Tests for the public API surface of the marketsurge package."""

# pyright: reportMissingImports=false


def test_import_no_side_effects(capsys):
    """Test that importing marketsurge triggers no output or side effects."""

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_all_exports_importable():
    """Test that every name in __all__ is actually importable from the package."""
    import tickerscope

    for name in tickerscope.__all__:
        obj = getattr(tickerscope, name)
        assert obj is not None, f"{name} is None"
    print(f"OK - {len(tickerscope.__all__)} exports verified")


def test_pattern_hierarchy_exports_present():
    import tickerscope

    expected_exports = {
        "CupPattern",
        "DoubleBottomPattern",
        "AscendingBasePattern",
        "IpoBasePattern",
        "TightArea",
    }
    assert expected_exports.issubset(set(tickerscope.__all__))


def test_client_importable_from_package():
    """Test that TickerScopeClient and AsyncTickerScopeClient can be imported."""
    from tickerscope import TickerScopeClient, AsyncTickerScopeClient

    assert TickerScopeClient is not None
    assert AsyncTickerScopeClient is not None


def test_internal_modules_not_in_all():
    """Test that internal modules are not in __all__."""
    import tickerscope

    internal = [n for n in tickerscope.__all__ if n.startswith("_")]
    assert internal == [], f"Internal names in __all__: {internal}"

    # Also verify formatting/CLI functions not present
    assert "main" not in tickerscope.__all__
    assert "format_list_table" not in tickerscope.__all__
    assert "get_list" not in tickerscope.__all__
    assert "get_stock_data" not in tickerscope.__all__
    assert "get_ownership" not in tickerscope.__all__
