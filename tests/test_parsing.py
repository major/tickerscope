"""Tests for response parsing functions."""

# pyright: reportMissingImports=false

import pytest

from tickerscope._exceptions import APIError, SymbolNotFoundError
from tickerscope._models import CupPattern
from tickerscope._parsing import (
    _safe_date_value,
    parse_active_alerts_response,
    parse_adhoc_screen_response,
    parse_chart_data_response,
    parse_chart_markups_response,
    parse_coach_tree_response,
    parse_fundamentals_response,
    parse_layouts_response,
    parse_nav_tree_response,
    parse_ownership_response,
    parse_panels_response,
    parse_rs_rating_history_response,
    parse_screen_result_response,
    parse_screens_response,
    parse_server_time_response,
    parse_stock_response,
    parse_triggered_alerts_response,
    parse_watchlist_detail_response,
    parse_watchlists_response,
    parse_watchlist_response,
)


# ---------------------------------------------------------------------------
# Cross-cutting: all parsers reject GraphQL error responses
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "parser,extra_args",
    [
        pytest.param(parse_stock_response, ("SYM",), id="stock"),
        pytest.param(parse_chart_data_response, ("SYM",), id="chart_data"),
        pytest.param(parse_fundamentals_response, ("SYM",), id="fundamentals"),
        pytest.param(parse_active_alerts_response, (), id="active_alerts"),
        pytest.param(parse_triggered_alerts_response, (), id="triggered_alerts"),
        pytest.param(parse_layouts_response, (), id="layouts"),
        pytest.param(parse_chart_markups_response, (), id="chart_markups"),
        pytest.param(parse_panels_response, (), id="panels"),
        pytest.param(parse_screens_response, (), id="screens"),
        pytest.param(parse_screen_result_response, (), id="screen_result"),
        pytest.param(
            parse_watchlist_detail_response, ("wl-id",), id="watchlist_detail"
        ),
        pytest.param(parse_watchlists_response, (), id="watchlist_names"),
        pytest.param(
            parse_rs_rating_history_response, ("SYM",), id="rs_rating_history"
        ),
        pytest.param(parse_server_time_response, (), id="server_time"),
        pytest.param(parse_nav_tree_response, (), id="nav_tree"),
        pytest.param(parse_coach_tree_response, (), id="coach_tree"),
        pytest.param(parse_adhoc_screen_response, (), id="adhoc_screen"),
    ],
)
def test_graphql_errors_raise_api_error(parser, extra_args) -> None:
    """All parsers raise APIError when the response contains GraphQL errors."""
    errors = [{"message": "bad query"}]
    with pytest.raises(APIError) as exc_info:
        parser({"errors": errors}, *extra_args)
    assert exc_info.value.errors == errors


# ---------------------------------------------------------------------------
# Stock parsing
# ---------------------------------------------------------------------------


def test_parse_stock_response_real_fixture(stock_response) -> None:
    """Parse the real stock fixture into StockData."""
    stock = parse_stock_response(stock_response, "TEST")

    assert stock.symbol == "TEST"
    assert stock.ratings is not None
    assert stock.ratings.composite == 95
    assert stock.ratings.rs == 92
    assert stock.ratings.smr == "A"
    assert stock.company is not None
    assert stock.company.name == "Alphabet, Inc."
    assert isinstance(stock.patterns, list)
    assert len(stock.patterns) >= 0
    assert isinstance(stock.patterns[0], CupPattern)
    assert isinstance(stock.tight_areas, list)
    assert stock.pricing is not None
    assert stock.pricing.ant_dates == ["2026-03-20", "2026-03-19", "2026-01-29"]


def test_parse_stock_response_empty_market_data() -> None:
    """Raise SymbolNotFoundError when marketData is empty."""
    try:
        parse_stock_response({"data": {"marketData": []}}, "FAKE")
    except SymbolNotFoundError as exc:
        assert "FAKE" in str(exc)
    else:
        raise AssertionError("Expected SymbolNotFoundError")


def test_parse_watchlist_response_empty() -> None:
    """Return empty list for watchlist responses with no rows."""
    result = parse_watchlist_response(
        {"data": {"marketDataAdhocScreen": {"responseValues": []}}}
    )

    assert result == []


def test_parse_watchlist_response_with_data() -> None:
    """Parse watchlist row values into typed WatchlistEntry data."""
    mock_row = [
        {"mdItem": {"name": "Symbol"}, "value": "AAPL"},
        {"mdItem": {"name": "CompanyName"}, "value": "Apple Inc"},
        {"mdItem": {"name": "CompositeRating"}, "value": 95},
    ]
    raw = {"data": {"marketDataAdhocScreen": {"responseValues": [mock_row]}}}

    result = parse_watchlist_response(raw)

    assert result[0].symbol == "AAPL"
    assert result[0].composite_rating == 95


def test_parse_ownership_response() -> None:
    """Parse ownership data and quarterly fund counts."""
    raw = {
        "data": {
            "marketData": [
                {
                    "ownership": {
                        "fundsFloatPercentHeld": {"formattedValue": "42.5%"},
                        "fundOwnershipSummary": [
                            {
                                "date": {"value": "2024-09-30"},
                                "numberOfFundsHeld": {"formattedValue": "1234"},
                            }
                        ],
                    }
                }
            ]
        }
    }

    result = parse_ownership_response(raw, "AAPL")

    assert result.symbol == "AAPL"
    assert result.funds_float_pct == "42.5%"
    assert len(result.quarterly_funds) == 1
    assert result.quarterly_funds[0].date == "2024-09-30"


def test_parse_ownership_not_found() -> None:
    """Raise SymbolNotFoundError when ownership marketData is empty."""
    try:
        parse_ownership_response({"data": {"marketData": []}}, "FAKE")
    except SymbolNotFoundError:
        pass
    else:
        raise AssertionError("Expected SymbolNotFoundError")


def test_parse_chart_data_response_real_fixture(chart_data_response) -> None:
    """Parse the chart data fixture into ChartData."""
    chart = parse_chart_data_response(chart_data_response, "TEST")

    assert chart.symbol == "TEST"
    assert chart.time_series is not None
    assert chart.time_series.period == "P1D"
    assert len(chart.time_series.data_points) == 3

    first = chart.time_series.data_points[0]
    assert first.open == 141.2500019775
    assert first.high == 143.864502014103
    assert first.low == 140.214501963003
    assert first.close == 142.966002001524
    assert first.volume == 29194839.5912722

    assert chart.quote is not None
    assert chart.quote.trade_date_time == "2026-03-20T17:05:20.717-04:00"
    assert chart.quote.timeliness == "DELAYED"
    assert chart.quote.quote_type == "REGULAR_SESSION"
    assert chart.quote.last == 6506.48
    assert chart.quote.volume == 10133392227.0


def test_parse_chart_data_response_empty_market_data() -> None:
    """Raise SymbolNotFoundError when marketData is empty for chart data."""
    try:
        parse_chart_data_response({"data": {"marketData": []}}, "FAKE")
    except SymbolNotFoundError as exc:
        assert "FAKE" in str(exc)
    else:
        raise AssertionError("Expected SymbolNotFoundError")


def test_parse_chart_data_response_no_benchmark(chart_data_response) -> None:
    """Single-symbol response has no benchmark_time_series."""
    chart = parse_chart_data_response(chart_data_response, "TEST")
    assert chart.benchmark_time_series is None


def test_parse_chart_data_response_with_benchmark() -> None:
    """Second marketData item is parsed as benchmark_time_series."""
    raw = {
        "data": {
            "marketData": [
                {
                    "pricing": {
                        "timeSeries": {
                            "period": "P1D",
                            "dataPoints": [
                                {
                                    "startDateTime": "2026-01-02",
                                    "endDateTime": "2026-01-02",
                                    "open": {"value": 50.0},
                                    "high": {"value": 52.0},
                                    "low": {"value": 49.0},
                                    "last": {"value": 51.0},
                                    "volume": {"value": 1000000},
                                }
                            ],
                        },
                        "quote": None,
                        "premarketQuote": None,
                        "postmarketQuote": None,
                        "currentMarketState": None,
                    }
                },
                {
                    "pricing": {
                        "timeSeries": {
                            "period": "P1D",
                            "dataPoints": [
                                {
                                    "startDateTime": "2026-01-02",
                                    "endDateTime": "2026-01-02",
                                    "open": {"value": 5800.0},
                                    "high": {"value": 5850.0},
                                    "low": {"value": 5780.0},
                                    "last": {"value": 5830.0},
                                    "volume": {"value": 3000000000},
                                }
                            ],
                        }
                    }
                },
            ]
        }
    }
    chart = parse_chart_data_response(raw, "TEST")

    assert chart.time_series is not None
    assert chart.time_series.data_points[0].close == 51.0

    assert chart.benchmark_time_series is not None
    assert len(chart.benchmark_time_series.data_points) == 1
    assert chart.benchmark_time_series.data_points[0].close == 5830.0
    assert chart.benchmark_time_series.period == "P1D"


def test_parse_chart_data_response_null_quotes(chart_data_response) -> None:
    """Return None for pre/post-market quotes when API values are null."""
    chart = parse_chart_data_response(chart_data_response, "TEST")

    assert chart.premarket_quote is None
    assert chart.postmarket_quote is None


def test_parse_fundamentals_response_real_fixture(fundamentals_response) -> None:
    """Parse the real fundamentals fixture into FundamentalData."""
    result = parse_fundamentals_response(fundamentals_response, "GOOGL")

    assert result.symbol == "GOOGL"
    assert result.company_name == "Alphabet, Inc."
    assert len(result.reported_earnings) == 7
    assert len(result.reported_sales) == 7
    assert len(result.eps_estimates) == 2
    assert len(result.sales_estimates) == 2

    first_earnings = result.reported_earnings[0]
    assert first_earnings.value == 10.81
    assert first_earnings.pct_change_yoy == 0.3445
    assert first_earnings.period_offset == "P1Y_AGO"
    assert first_earnings.period_end_date == "2025-12-31"

    first_eps_est = result.eps_estimates[0]
    assert first_eps_est.revision_direction == "UP"
    assert first_eps_est.period == "P1Y"


def test_parse_fundamentals_response_empty_market_data() -> None:
    """Raise SymbolNotFoundError when marketData is empty."""
    try:
        parse_fundamentals_response({"data": {"marketData": []}}, "FAKE")
    except SymbolNotFoundError as exc:
        assert "FAKE" in str(exc)
    else:
        raise AssertionError("Expected SymbolNotFoundError")


def test_parse_active_alerts_response_real_fixture(active_alerts_response) -> None:
    """Parse the real active alerts fixture into AlertSubscriptionList."""
    result = parse_active_alerts_response(active_alerts_response)

    assert result.num_subscriptions == 3
    assert result.remaining_subscriptions == 747
    assert len(result.subscriptions) == 3

    first = result.subscriptions[0]
    assert len(first.delivery_preferences) == 3
    assert first.delivery_preferences[0].method == "email"
    assert first.delivery_preferences[0].type == "realtime"
    assert first.criteria is not None
    assert first.criteria.alert_type == "realtime_price"
    assert first.criteria.term is not None
    assert first.criteria.term.instrument is not None
    assert first.criteria.term.instrument.ticker == "VAL"
    assert first.criteria.term.instrument.charting_symbol == "STOCK/US/XNYS/VAL"
    assert first.criteria.term.value == "61.70"
    assert first.criteria.term.operator == "greater_than_or_equal_to"


def test_parse_active_alerts_response_company_term(active_alerts_response) -> None:
    """Verify CompanyTermCriteria subscriptions have instrument=None."""
    result = parse_active_alerts_response(active_alerts_response)

    event_sub = next(
        s
        for s in result.subscriptions
        if s.criteria and s.criteria.alert_type == "market_data_event"
    )
    assert event_sub.criteria is not None
    assert event_sub.criteria.term is not None
    assert event_sub.criteria.term.instrument is None
    assert event_sub.criteria.term.value == "breakaway_gap"
    assert event_sub.criteria.term.field == "event"


def test_parse_active_alerts_response_empty() -> None:
    """Return empty AlertSubscriptionList when no subscriptions exist."""
    raw = {
        "data": {
            "user": {
                "followSubscriptionsWithCount": {
                    "subscriptions": [],
                    "numSubscriptions": 0,
                    "remainingSubscriptions": 750,
                }
            }
        }
    }
    result = parse_active_alerts_response(raw)

    assert result.subscriptions == []
    assert result.num_subscriptions == 0
    assert result.remaining_subscriptions == 750


def test_parse_triggered_alerts_response_real_fixture(
    triggered_alerts_response,
) -> None:
    """Parse the real triggered alerts fixture into TriggeredAlertList."""
    result = parse_triggered_alerts_response(triggered_alerts_response)

    assert result.cursor_id is None
    assert len(result.alerts) == 3

    first = result.alerts[0]
    assert first.alert_id == "01KM5Q1077RR24AJWY7ZTE6A7P"
    assert first.alert_type == "realtime_price"
    assert isinstance(first.payload, dict)
    assert first.payload["symbol"] == "SEDG"
    assert first.payload["price"] == "48.6000"
    assert first.delivery_preference is not None
    assert first.delivery_preference.method == "email"
    assert first.delivery_preference.type == "realtime"
    assert first.term is not None
    assert first.term.dj_key == "13-14381691"
    assert first.term.instrument is not None
    assert first.term.instrument.ticker == "SEDG"
    assert first.term.instrument.charting_symbol == "STOCK/US/XNAS/SEDG"
    assert first.delivered is False
    assert first.viewed is False
    assert first.ttl == 1776605415

    second = result.alerts[1]
    assert second.alert_type == "market_data_event"
    assert second.term is not None
    assert second.term.dj_key is None
    assert second.term.instrument is None
    assert second.term.value == "breaking_out_today"
    assert second.term.field == "event"

    third = result.alerts[2]
    assert third.viewed is True


def test_parse_triggered_alerts_response_empty() -> None:
    """Return TriggeredAlertList with empty alerts list when none exist."""
    raw = {"data": {"user": {"followAlerts": {"cursorId": None, "alerts": []}}}}
    result = parse_triggered_alerts_response(raw)

    assert result.cursor_id is None
    assert result.alerts == []


def test_parse_layouts_response_real_fixture(layouts_response) -> None:
    """Parse the real layouts fixture into Layout list."""
    layouts = parse_layouts_response(layouts_response)

    assert len(layouts) == 1
    layout = layouts[0]
    assert layout.id == "fff08008-be89-4076-9803-58cf47618552"
    assert layout.name == "Funds Focus"
    assert layout.site == "marketsurge"
    assert len(layout.columns) == 16
    assert layout.columns[0].md_item_id == "61"
    assert layout.columns[0].name == "Current Price"
    assert layout.columns[0].width == 60
    assert layout.columns[0].locked is False
    assert layout.columns[0].visible is True


def test_parse_layouts_response_empty() -> None:
    """Return empty list for layouts responses with no layouts."""
    result = parse_layouts_response({"data": {"user": {"marketDataLayouts": []}}})

    assert result == []


def test_parse_chart_markups_response_empty(chart_markups_response) -> None:
    """Parse empty chart markups response with no markups."""
    result = parse_chart_markups_response(chart_markups_response)

    assert result.cursor_id is None
    assert result.markups == []


def test_parse_chart_markups_response_with_data() -> None:
    """Parse chart markups with populated data, keeping data field as string."""
    raw = {
        "data": {
            "user": {
                "chartMarkups": {
                    "cursorId": "next-page-123",
                    "chartMarkups": [
                        {
                            "id": "markup-1",
                            "name": "Support Line",
                            "data": '{"type":"line","points":[1,2,3]}',
                            "frequency": "DAILY",
                            "site": "marketsurge",
                            "createdAt": "2024-01-15T10:30:00Z",
                            "updatedAt": "2024-01-20T14:45:00Z",
                        },
                        {
                            "id": "markup-2",
                            "name": None,
                            "data": '{"type":"box"}',
                            "frequency": None,
                            "site": None,
                            "createdAt": None,
                            "updatedAt": None,
                        },
                    ],
                }
            }
        }
    }

    result = parse_chart_markups_response(raw)

    assert result.cursor_id == "next-page-123"
    assert len(result.markups) == 2

    markup1 = result.markups[0]
    assert markup1.id == "markup-1"
    assert markup1.name == "Support Line"
    assert markup1.data == '{"type":"line","points":[1,2,3]}'
    assert isinstance(markup1.data, str)
    assert markup1.frequency == "DAILY"
    assert markup1.site == "marketsurge"
    assert markup1.created_at == "2024-01-15T10:30:00Z"
    assert markup1.updated_at == "2024-01-20T14:45:00Z"

    markup2 = result.markups[1]
    assert markup2.id == "markup-2"
    assert markup2.name is None
    assert markup2.data == '{"type":"box"}'
    assert isinstance(markup2.data, str)


class TestSafeDateValue:
    """Tests for the _safe_date_value() sentinel filtering helper."""

    def test_sentinel_date_returns_none(self) -> None:
        """The '0001-01-01' sentinel is normalized to None."""
        assert _safe_date_value({"value": "0001-01-01"}) is None

    def test_valid_date_passes_through(self) -> None:
        """A valid date string is returned unchanged."""
        assert _safe_date_value({"value": "2025-01-15"}) == "2025-01-15"

    def test_none_input_returns_none(self) -> None:
        """None input returns None (delegated to _safe_value)."""
        assert _safe_date_value(None) is None

    def test_empty_dict_returns_none(self) -> None:
        """Empty dict with no 'value' key returns None."""
        assert _safe_date_value({}) is None

    def test_non_dict_returns_none(self) -> None:
        """Non-dict input returns None (delegated to _safe_value)."""
        assert _safe_date_value("not-a-dict") is None  # type: ignore[arg-type]
