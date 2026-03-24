"""Tests for to_dict() and to_json() serialization across all dataclass models."""

from __future__ import annotations

import json

import pytest

from tickerscope._models import (
    BasicOwnership,
    Company,
    EstimatePeriod,
    Fundamentals,
    Pattern,
    PricePercentChanges,
    Ratings,
    ReportedPeriod,
)

_COMPANY_WITH_IPO = Company(
    name="Acme",
    industry=None,
    sector=None,
    industry_group_rank=None,
    industry_group_rs=None,
    industry_group_rs_letter=None,
    description=None,
    website=None,
    address=None,
    address2=None,
    phone=None,
    ipo_date=None,
    ipo_price=25.0,
    ipo_price_formatted="$25.00",
)
_CUP_PATTERN = Pattern(
    type="Cup",
    stage=1,
    base_number=1,
    status="Complete",
    pivot_price=150.0,
    pivot_price_formatted="$150.00",
    pivot_date="2024-01-01",
    base_start_date="2023-06-01",
    base_end_date="2024-01-01",
    base_length=30,
)
_BASIC_OWNERSHIP = BasicOwnership(
    funds_float_pct=43.87, funds_float_pct_formatted="43.87%"
)
_REPORTED_PERIOD = ReportedPeriod(
    value=2.5,
    formatted_value="$2.50",
    pct_change_yoy=15.2,
    formatted_pct_change="15.2%",
    period_offset="0",
    period_end_date="2024-12-31",
)
_ESTIMATE_PERIOD = EstimatePeriod(
    value=3.0,
    formatted_value="$3.00",
    pct_change_yoy=10.0,
    formatted_pct_change="10.0%",
    period_offset="1",
    period=None,
    revision_direction="UP",
)


class TestRatingsSerialize:
    """Verify basic to_dict() output on Ratings (simplest leaf dataclass)."""

    def test_to_dict_returns_dict(self) -> None:
        """to_dict() return type is a plain dict."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        assert isinstance(r.to_dict(), dict)

    def test_to_dict_contains_all_fields(self) -> None:
        """All non-None Ratings fields appear in the dict with correct values."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        d = r.to_dict()
        assert d == {"composite": 95, "eps": 99, "rs": 89, "smr": "A", "ad": "B+"}


class TestNoneOmission:
    """Verify that None-valued fields are excluded from to_dict() output."""

    def test_none_fields_excluded_from_dict(self) -> None:
        """Fields set to None do not appear in the serialized dict."""
        r = Ratings(composite=95, eps=None, rs=89, smr=None, ad="B")
        d = r.to_dict()
        assert "eps" not in d
        assert "smr" not in d
        assert d == {"composite": 95, "rs": 89, "ad": "B"}

    def test_all_none_returns_empty_dict(self) -> None:
        """When every field is None, to_dict() produces an empty dict."""
        r = Ratings(composite=None, eps=None, rs=None, smr=None, ad=None)
        assert r.to_dict() == {}


class TestNestedSerialization:
    """Verify nested dataclass instances are recursively serialized."""

    def test_nested_dataclass_serialized_as_dict(self, minimal_stock) -> None:
        """A nested Ratings inside StockData becomes a nested plain dict."""
        stock = minimal_stock()
        d = stock.to_dict()
        assert isinstance(d["ratings"], dict)
        assert d["ratings"]["composite"] == 95

    def test_none_nested_omitted(self, minimal_stock) -> None:
        """Nested fields that are None are excluded from the top-level dict."""
        stock = minimal_stock()
        d = stock.to_dict()
        assert "company" not in d
        assert "pricing" not in d
        assert "financials" not in d


class TestListSerialization:
    """Verify lists of dataclasses serialize into lists of dicts."""

    def test_list_of_dataclasses_serialized(self, minimal_stock) -> None:
        """A list[Pattern] becomes a list[dict] in the serialized output."""
        stock = minimal_stock(patterns=[_CUP_PATTERN])
        d = stock.to_dict()
        assert isinstance(d["patterns"], list)
        assert len(d["patterns"]) == 1
        assert isinstance(d["patterns"][0], dict)

    def test_empty_list_included(self, minimal_stock) -> None:
        """An empty patterns list still appears in the output dict."""
        stock = minimal_stock(patterns=[])
        d = stock.to_dict()
        assert d["patterns"] == []


class TestFormattedSuffixDrop:
    """Verify raw fields are dropped when their _formatted counterpart exists."""

    def test_raw_dropped_when_formatted_present(self, minimal_pricing) -> None:
        """market_cap is kept when market_cap_formatted is non-None."""
        p = minimal_pricing(market_cap=3.2e12, market_cap_formatted="$3.2T")
        d = p.to_dict()
        assert "market_cap" in d
        assert d.get("market_cap_formatted") == "$3.2T"

    def test_raw_kept_when_formatted_none(self, minimal_pricing) -> None:
        """market_cap is kept when market_cap_formatted is None (omitted)."""
        p = minimal_pricing(market_cap=3.2e12, market_cap_formatted=None)
        d = p.to_dict()
        assert "market_cap" in d
        assert "market_cap_formatted" not in d

    def test_all_5_pricing_pairs_dropped(self, minimal_pricing) -> None:
        """All 5 raw/formatted pairs in Pricing keep both raw and formatted values."""
        p = minimal_pricing(
            market_cap=3.2e12,
            market_cap_formatted="$3.2T",
            avg_dollar_volume_50d=1.25e10,
            avg_dollar_volume_50d_formatted="$12.5B",
            up_down_volume_ratio=1.5,
            up_down_volume_ratio_formatted="1.5",
            atr_percent_21d=2.3,
            atr_percent_21d_formatted="2.3%",
            short_interest_percent_float=1.2,
            short_interest_percent_float_formatted="1.2%",
        )
        d = p.to_dict()
        for raw in [
            "market_cap",
            "avg_dollar_volume_50d",
            "up_down_volume_ratio",
            "atr_percent_21d",
            "short_interest_percent_float",
        ]:
            assert raw in d, f"{raw} should be present"

    @pytest.mark.parametrize(
        ("model", "raw_field", "fmt_field", "fmt_value"),
        [
            (_COMPANY_WITH_IPO, "ipo_price", "ipo_price_formatted", "$25.00"),
            (_CUP_PATTERN, "pivot_price", "pivot_price_formatted", "$150.00"),
            (
                _BASIC_OWNERSHIP,
                "funds_float_pct",
                "funds_float_pct_formatted",
                "43.87%",
            ),
        ],
    )
    def test_formatted_field_preserved(
        self, model, raw_field, fmt_field, fmt_value
    ) -> None:
        """Raw field is kept and formatted field has expected value when both are present."""
        d = model.to_dict()
        assert raw_field in d
        assert d[fmt_field] == fmt_value


class TestFormattedPrefixDrop:
    """Verify raw fields are dropped when their formatted_ prefix counterpart exists."""

    @pytest.mark.parametrize("model", [_REPORTED_PERIOD, _ESTIMATE_PERIOD])
    def test_raw_kept_when_formatted_present(self, model) -> None:
        """Raw value and pct_change_yoy are kept when formatted versions exist."""
        d = model.to_dict()
        assert "value" in d
        assert "pct_change_yoy" in d

    def test_reported_period_keeps_raw_when_formatted_none(self) -> None:
        """ReportedPeriod keeps raw value when formatted_value is None."""
        rp = ReportedPeriod(
            value=2.5,
            formatted_value=None,
            pct_change_yoy=15.2,
            formatted_pct_change=None,
            period_offset="0",
            period_end_date="2024-12-31",
        )
        d = rp.to_dict()
        assert d["value"] == 2.5
        assert d["pct_change_yoy"] == 15.2
        assert "formatted_value" not in d
        assert "formatted_pct_change" not in d


class TestOrphanField:
    """Verify orphan formatted fields (no raw counterpart) are preserved."""

    def test_debt_percent_formatted_preserved(self) -> None:
        """Fundamentals.debt_percent_formatted has no raw pair and must not be dropped."""
        f = Fundamentals(
            r_and_d_percent_last_qtr=5.2,
            r_and_d_percent_last_qtr_formatted="5.2%",
            debt_percent_formatted="12.3%",
            new_ceo_date=None,
        )
        d = f.to_dict()
        assert "debt_percent_formatted" in d
        assert d["debt_percent_formatted"] == "12.3%"
        assert "r_and_d_percent_last_qtr" in d  # raw kept since formatted exists

    def test_debt_percent_formatted_omitted_when_none(self) -> None:
        """Orphan debt_percent_formatted is omitted when None (standard omit_none)."""
        f = Fundamentals(
            r_and_d_percent_last_qtr=None,
            r_and_d_percent_last_qtr_formatted=None,
            debt_percent_formatted=None,
            new_ceo_date=None,
        )
        d = f.to_dict()
        assert d == {}


class TestToJson:
    """Verify to_json() returns valid JSON strings consistent with to_dict()."""

    def test_to_json_basic(self) -> None:
        """to_json() returns valid JSON string, with correct values and None fields omitted."""
        r = Ratings(composite=95, eps=None, rs=89, smr=None, ad="B")
        j = r.to_json()
        assert isinstance(j, str)
        parsed = json.loads(j)
        assert parsed == {"composite": 95, "rs": 89, "ad": "B"}
        assert "eps" not in parsed
        assert "smr" not in parsed

    def test_to_json_nested_stock_data(self, minimal_stock) -> None:
        """StockData.to_json() serializes nested structures correctly."""
        stock = minimal_stock()
        parsed = json.loads(stock.to_json())
        assert parsed["symbol"] == "TEST"
        assert isinstance(parsed["ratings"], dict)
        assert "company" not in parsed  # None → omitted


class TestRoundTrip:
    """Smoke tests for to_dict() → from_dict() round-trip fidelity."""

    def test_ratings_round_trip(self) -> None:
        """Ratings with all fields populated survives a round-trip unchanged."""
        r = Ratings(composite=95, eps=99, rs=89, smr="A", ad="B+")
        d = r.to_dict()
        reconstructed = Ratings.from_dict(d)
        assert reconstructed == r

    def test_price_percent_changes_round_trip(self) -> None:
        """PricePercentChanges with all fields populated survives a round-trip."""
        ppc = PricePercentChanges(
            ytd=12.5,
            mtd=3.2,
            qtd=5.0,
            wtd=1.1,
            vs_1d=-0.5,
            vs_1m=2.0,
            vs_3m=8.3,
            vs_year_high=-5.0,
            vs_year_low=45.0,
        )
        d = ppc.to_dict()
        reconstructed = PricePercentChanges.from_dict(d)
        assert reconstructed == ppc


class TestOmitNoneParameter:
    """Tests for runtime omit_none parameter on to_dict() and to_json()."""

    def test_to_dict_default_omits_none_backward_compat(self) -> None:
        """model.to_dict() with no args omits None fields (backward compat)."""
        r = Ratings(composite=99, eps=None, rs=None, smr=None, ad=None)
        d = r.to_dict()
        assert "composite" in d
        assert d["composite"] == 99
        assert "eps" not in d

    @pytest.mark.parametrize(
        ("method", "kwargs"),
        [("to_dict", {"omit_none": False}), ("to_json", {"omit_none": False})],
    )
    def test_omit_none_false_includes_nulls(self, method, kwargs) -> None:
        """to_dict/to_json with omit_none=False includes None fields as explicit nulls."""
        r = Ratings(composite=99, eps=None, rs=None, smr=None, ad=None)
        result = getattr(r, method)(**kwargs)
        if method == "to_json":
            result = json.loads(result)
        assert "composite" in result
        assert result["composite"] == 99
        assert "eps" in result
        assert result["eps"] is None

    def test_nested_propagation_with_real_model(self, minimal_stock) -> None:
        """StockData.to_dict(omit_none=False) propagates nulls to nested Ratings."""
        s = minimal_stock(
            ratings=Ratings(composite=99, eps=None, rs=None, smr=None, ad=None),
        )
        d = s.to_dict(omit_none=False)
        assert "ratings" in d
        ratings_dict = d["ratings"]
        assert "composite" in ratings_dict
        assert ratings_dict["composite"] == 99
        assert "eps" in ratings_dict
        assert ratings_dict["eps"] is None
