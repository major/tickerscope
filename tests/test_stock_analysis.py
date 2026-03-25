"""Tests for get_stock_analysis() composite convenience methods."""

from __future__ import annotations

# pyright: reportMissingImports=false

from unittest.mock import AsyncMock, MagicMock

import pytest


def test_get_stock_analysis_all_success(sync_client):
    """Return StockAnalysis with stock, fundamentals, and ownership on success."""
    from tickerscope import FundamentalData, OwnershipData, StockAnalysis, StockData

    stock = MagicMock(spec=StockData)
    fundamentals = MagicMock(spec=FundamentalData)
    ownership = MagicMock(spec=OwnershipData)

    sync_client.get_stock = MagicMock(return_value=stock)
    sync_client.get_fundamentals = MagicMock(return_value=fundamentals)
    sync_client.get_ownership = MagicMock(return_value=ownership)

    result = sync_client.get_stock_analysis("NVDA")

    assert isinstance(result, StockAnalysis)
    assert result.symbol == "NVDA"
    assert result.stock is stock
    assert result.fundamentals is fundamentals
    assert result.ownership is ownership
    assert result.errors == []


def test_get_stock_analysis_fundamentals_failure(sync_client):
    """Capture fundamentals failure but still return stock and ownership."""
    from tickerscope import OwnershipData, StockData

    stock = MagicMock(spec=StockData)
    ownership = MagicMock(spec=OwnershipData)

    sync_client.get_stock = MagicMock(return_value=stock)
    sync_client.get_fundamentals = MagicMock(side_effect=RuntimeError("fund boom"))
    sync_client.get_ownership = MagicMock(return_value=ownership)

    result = sync_client.get_stock_analysis("AAPL")

    assert result.stock is stock
    assert result.fundamentals is None
    assert result.ownership is ownership
    assert result.errors == ["fund boom"]


def test_get_stock_analysis_ownership_failure(sync_client):
    """Capture ownership failure but still return stock and fundamentals."""
    from tickerscope import FundamentalData, StockData

    stock = MagicMock(spec=StockData)
    fundamentals = MagicMock(spec=FundamentalData)

    sync_client.get_stock = MagicMock(return_value=stock)
    sync_client.get_fundamentals = MagicMock(return_value=fundamentals)
    sync_client.get_ownership = MagicMock(side_effect=RuntimeError("own boom"))

    result = sync_client.get_stock_analysis("MSFT")

    assert result.stock is stock
    assert result.fundamentals is fundamentals
    assert result.ownership is None
    assert result.errors == ["own boom"]


def test_get_stock_analysis_stock_failure_reraises(sync_client):
    """Re-raise stock failure without swallowing the exception."""
    sync_client.get_stock = MagicMock(side_effect=RuntimeError("stock boom"))

    with pytest.raises(RuntimeError, match="stock boom"):
        sync_client.get_stock_analysis("TSLA")


def test_stock_analysis_to_dict_output():
    """Serialize StockAnalysis with expected keys and error list."""
    from tickerscope import StockAnalysis, StockData

    stock = StockData(
        symbol="AMD",
        ratings=None,
        company=None,
        pricing=None,
        financials=None,
        corporate_actions=None,
        industry=None,
        ownership=None,
        fundamentals=None,
        patterns=[],
        tight_areas=[],
    )

    payload = StockAnalysis(
        symbol="AMD",
        stock=stock,
        fundamentals=None,
        ownership=None,
        errors=["fundamentals unavailable", "ownership unavailable"],
    ).to_dict()

    assert payload == {
        "symbol": "AMD",
        "stock": {
            "symbol": "AMD",
            "patterns": [],
            "tight_areas": [],
        },
        "errors": ["fundamentals unavailable", "ownership unavailable"],
    }


@pytest.mark.asyncio
async def test_async_get_stock_analysis_all_success(async_client):
    """Return StockAnalysis with all sections when async calls succeed."""
    from tickerscope import FundamentalData, OwnershipData, StockData

    stock = MagicMock(spec=StockData)
    fundamentals = MagicMock(spec=FundamentalData)
    ownership = MagicMock(spec=OwnershipData)

    async_client.get_stock = AsyncMock(return_value=stock)
    async_client.get_fundamentals = AsyncMock(return_value=fundamentals)
    async_client.get_ownership = AsyncMock(return_value=ownership)

    result = await async_client.get_stock_analysis("NVDA")

    assert result.stock is stock
    assert result.fundamentals is fundamentals
    assert result.ownership is ownership
    assert result.errors == []


@pytest.mark.asyncio
async def test_async_get_stock_analysis_fundamentals_failure(async_client):
    """Capture async fundamentals failure while preserving other data."""
    from tickerscope import OwnershipData, StockData

    stock = MagicMock(spec=StockData)
    ownership = MagicMock(spec=OwnershipData)

    async_client.get_stock = AsyncMock(return_value=stock)
    async_client.get_fundamentals = AsyncMock(side_effect=RuntimeError("fund boom"))
    async_client.get_ownership = AsyncMock(return_value=ownership)

    result = await async_client.get_stock_analysis("AAPL")

    assert result.stock is stock
    assert result.fundamentals is None
    assert result.ownership is ownership
    assert result.errors == ["fund boom"]


@pytest.mark.asyncio
async def test_async_get_stock_analysis_ownership_failure(async_client):
    """Capture async ownership failure while preserving other data."""
    from tickerscope import FundamentalData, StockData

    stock = MagicMock(spec=StockData)
    fundamentals = MagicMock(spec=FundamentalData)

    async_client.get_stock = AsyncMock(return_value=stock)
    async_client.get_fundamentals = AsyncMock(return_value=fundamentals)
    async_client.get_ownership = AsyncMock(side_effect=RuntimeError("own boom"))

    result = await async_client.get_stock_analysis("MSFT")

    assert result.stock is stock
    assert result.fundamentals is fundamentals
    assert result.ownership is None
    assert result.errors == ["own boom"]


@pytest.mark.asyncio
async def test_async_get_stock_analysis_stock_failure_reraises(async_client):
    """Re-raise async stock failure and do not return StockAnalysis."""
    async_client.get_stock = AsyncMock(side_effect=RuntimeError("stock boom"))
    async_client.get_fundamentals = AsyncMock(return_value=None)
    async_client.get_ownership = AsyncMock(return_value=None)

    with pytest.raises(RuntimeError, match="stock boom"):
        await async_client.get_stock_analysis("TSLA")
