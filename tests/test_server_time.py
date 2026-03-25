"""Tests for GetServerDateTime endpoint."""

# pyright: reportMissingImports=false

import datetime

import pytest
import respx
import httpx

from tickerscope._parsing import parse_server_time_response
from tickerscope._exceptions import APIError

GRAPHQL_URL = "https://shared-data.dowjones.io/gateway/graphql"


def test_parse_server_time_fixture(server_time_response) -> None:
    """Parse real server time fixture into timezone-aware datetime."""
    result = parse_server_time_response(server_time_response)
    assert isinstance(result, datetime.datetime)
    assert result.tzinfo is not None
    assert result.year == 2026
    assert result.month == 3
    assert result.day == 24


def test_parse_server_time_missing_datetime() -> None:
    """Raise APIError when ibdGetServerDateTime is missing."""
    raw = {"data": {"ibdGetServerDateTime": None}}
    with pytest.raises(APIError) as exc_info:
        parse_server_time_response(raw)
    assert "Server returned no datetime" in str(exc_info.value)


def test_parse_server_time_empty_string() -> None:
    """Raise APIError when ibdGetServerDateTime is empty string."""
    raw = {"data": {"ibdGetServerDateTime": ""}}
    with pytest.raises(APIError) as exc_info:
        parse_server_time_response(raw)
    assert "Server returned no datetime" in str(exc_info.value)


def test_parse_server_time_missing_data_key() -> None:
    """Raise APIError when data key is missing."""
    raw = {}
    with pytest.raises(APIError) as exc_info:
        parse_server_time_response(raw)
    assert "Server returned no datetime" in str(exc_info.value)


def test_parse_server_time_graphql_errors() -> None:
    """Raise APIError when response contains GraphQL errors."""
    errors = [{"message": "bad query"}]
    with pytest.raises(APIError) as exc_info:
        parse_server_time_response({"errors": errors})
    assert exc_info.value.errors == errors


@respx.mock
def test_get_server_time_sync(server_time_response) -> None:
    """Sync client get_server_time() returns timezone-aware datetime."""
    from tickerscope import TickerScopeClient

    route = respx.post(GRAPHQL_URL).mock(
        return_value=httpx.Response(200, json=server_time_response)
    )

    with TickerScopeClient(jwt="fake-jwt") as client:
        result = client.get_server_time()

    assert isinstance(result, datetime.datetime)
    assert result.tzinfo is not None
    assert route.call_count == 1


@respx.mock
async def test_get_server_time_async(server_time_response) -> None:
    """Async client get_server_time() returns timezone-aware datetime."""
    from tickerscope import AsyncTickerScopeClient

    route = respx.post(GRAPHQL_URL).mock(
        return_value=httpx.Response(200, json=server_time_response)
    )

    async with AsyncTickerScopeClient(jwt="fake-jwt") as client:
        result = await client.get_server_time()

    assert isinstance(result, datetime.datetime)
    assert result.tzinfo is not None
    assert route.call_count == 1
