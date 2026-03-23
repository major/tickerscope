"""Smoke test to verify test infrastructure and fixtures load correctly."""


def test_fixtures_load(stock_response, stock_extracted):
    """Verify both JSON fixtures load and contain expected structure."""
    # Verify stock_response has expected structure
    assert "data" in stock_response
    assert "marketData" in stock_response["data"]
    assert isinstance(stock_response["data"]["marketData"], list)
    assert len(stock_response["data"]["marketData"]) > 0

    # Verify stock_extracted has expected structure (snake_case keys from parser)
    assert "symbol" in stock_extracted
    assert "ratings" in stock_extracted
    assert "company" in stock_extracted
    assert "pricing" in stock_extracted
    assert "financials" in stock_extracted
    assert "corporate_actions" in stock_extracted
    assert "industry" in stock_extracted
    assert "ownership" in stock_extracted
    assert "fundamentals" in stock_extracted
    assert "patterns" in stock_extracted


def test_fixtures_are_valid_json(stock_response, stock_extracted):
    """Verify fixtures are valid JSON and can be serialized."""
    import json

    # Should not raise
    json.dumps(stock_response)
    json.dumps(stock_extracted)
