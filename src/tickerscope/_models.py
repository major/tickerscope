"""Typed dataclass models for TickerScope API responses."""

from __future__ import annotations

import datetime
import json
from dataclasses import dataclass
from typing import Any

from mashumaro.config import BaseConfig  # pyright: ignore[reportMissingImports]
from mashumaro.mixins.dict import DataClassDictMixin  # pyright: ignore[reportMissingImports]

from tickerscope._dates import parse_date, parse_date_list, parse_datetime


@dataclass(frozen=True, slots=True)
class Ratings(DataClassDictMixin):
    """Stock composite, EPS, RS, SMR, and A/D ratings."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    composite: int | None
    eps: int | None
    rs: int | None
    smr: str | None
    ad: str | None


@dataclass(frozen=True, slots=True)
class Company(DataClassDictMixin):
    """Company profile information."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("ipo_price_formatted") is not None:
            d.pop("ipo_price", None)
        return d

    name: str | None
    industry: str | None
    sector: str | None
    industry_group_rank: int | None
    industry_group_rs: int | None
    industry_group_rs_letter: str | None
    description: str | None
    website: str | None
    address: str | None
    address2: str | None
    phone: str | None
    ipo_date: str | None
    ipo_price: float | None
    ipo_price_formatted: str | None

    @property
    def ipo_date_dt(self) -> datetime.date | None:
        """Parsed ipo_date as a date object, or None if unavailable."""
        return parse_date(self.ipo_date)


@dataclass(frozen=True, slots=True)
class PricePercentChanges(DataClassDictMixin):
    """Price percent changes vs various reference periods."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    ytd: float | None
    mtd: float | None
    qtd: float | None
    wtd: float | None
    vs_1d: float | None
    vs_1m: float | None
    vs_3m: float | None
    vs_year_high: float | None
    vs_year_low: float | None


@dataclass(frozen=True, slots=True)
class Pricing(DataClassDictMixin):
    """Pricing statistics and market data."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("market_cap_formatted") is not None:
            d.pop("market_cap", None)
        if d.get("avg_dollar_volume_50d_formatted") is not None:
            d.pop("avg_dollar_volume_50d", None)
        if d.get("up_down_volume_ratio_formatted") is not None:
            d.pop("up_down_volume_ratio", None)
        if d.get("atr_percent_21d_formatted") is not None:
            d.pop("atr_percent_21d", None)
        if d.get("short_interest_percent_float_formatted") is not None:
            d.pop("short_interest_percent_float", None)
        return d

    market_cap: float | None
    market_cap_formatted: str | None
    avg_dollar_volume_50d: float | None
    avg_dollar_volume_50d_formatted: str | None
    up_down_volume_ratio: float | None
    up_down_volume_ratio_formatted: str | None
    atr_percent_21d: float | None
    atr_percent_21d_formatted: str | None
    short_interest_percent_float: float | None
    short_interest_percent_float_formatted: str | None
    blue_dot_daily_dates: list[str | None]
    blue_dot_weekly_dates: list[str | None]
    price_percent_changes: PricePercentChanges | None
    volume_percent_change_vs_50d: float | None

    @property
    def blue_dot_daily_dates_dt(self) -> list[datetime.date | None]:
        """Parsed blue_dot_daily_dates as a list of date objects."""
        return parse_date_list(self.blue_dot_daily_dates)

    @property
    def blue_dot_weekly_dates_dt(self) -> list[datetime.date | None]:
        """Parsed blue_dot_weekly_dates as a list of date objects."""
        return parse_date_list(self.blue_dot_weekly_dates)


@dataclass(frozen=True, slots=True)
class Financials(DataClassDictMixin):
    """Financial metrics and earnings data."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    eps_due_date: str | None
    eps_due_date_status: str | None
    eps_last_reported_date: str | None
    eps_growth_rate: float | None
    sales_growth_rate_3y: float | None
    pre_tax_margin: float | None
    after_tax_margin: float | None
    gross_margin: float | None
    return_on_equity: float | None
    earnings_stability: int | None

    @property
    def eps_due_date_dt(self) -> datetime.date | None:
        """Parsed eps_due_date as a date object, or None if unavailable."""
        return parse_date(self.eps_due_date)

    @property
    def eps_last_reported_date_dt(self) -> datetime.date | None:
        """Parsed eps_last_reported_date as a date object, or None if unavailable."""
        return parse_date(self.eps_last_reported_date)


@dataclass(frozen=True, slots=True)
class Dividend(DataClassDictMixin):
    """Individual dividend event."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    ex_date: str | None
    amount: str | None
    change_indicator: str | None

    @property
    def ex_date_dt(self) -> datetime.date | None:
        """Parsed ex_date as a date object, or None if unavailable."""
        return parse_date(self.ex_date)


@dataclass(frozen=True, slots=True)
class CorporateActions(DataClassDictMixin):
    """Corporate action history (dividends, splits, spinoffs)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    next_ex_dividend_date: str | None
    dividends: list[Dividend]
    splits: list[str | None]
    spinoffs: list

    @property
    def next_ex_dividend_date_dt(self) -> datetime.date | None:
        """Parsed next_ex_dividend_date as a date object, or None if unavailable."""
        return parse_date(self.next_ex_dividend_date)


@dataclass(frozen=True, slots=True)
class Pattern(DataClassDictMixin):
    """Technical chart pattern detected by MarketSurge."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("pivot_price_formatted") is not None:
            d.pop("pivot_price", None)
        return d

    type: str | None
    stage: int | None
    base_number: int | None
    status: str | None
    pivot_price: float | None
    pivot_price_formatted: str | None
    pivot_date: str | None
    base_start_date: str | None
    base_end_date: str | None
    base_length: int | None

    @property
    def pivot_date_dt(self) -> datetime.date | None:
        """Parsed pivot_date as a date object, or None if unavailable."""
        return parse_date(self.pivot_date)

    @property
    def base_start_date_dt(self) -> datetime.date | None:
        """Parsed base_start_date as a date object, or None if unavailable."""
        return parse_date(self.base_start_date)

    @property
    def base_end_date_dt(self) -> datetime.date | None:
        """Parsed base_end_date as a date object, or None if unavailable."""
        return parse_date(self.base_end_date)


@dataclass(frozen=True, slots=True)
class Industry(DataClassDictMixin):
    """Industry group information."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    name: str | None
    sector: str | None
    code: str | None
    number_of_stocks: int | None


@dataclass(frozen=True, slots=True)
class BasicOwnership(DataClassDictMixin):
    """Basic fund ownership metrics (from stock data query)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("funds_float_pct_formatted") is not None:
            d.pop("funds_float_pct", None)
        return d

    funds_float_pct: float | None
    funds_float_pct_formatted: str | None


@dataclass(frozen=True, slots=True)
class Fundamentals(DataClassDictMixin):
    """Fundamental financial data."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("r_and_d_percent_last_qtr_formatted") is not None:
            d.pop("r_and_d_percent_last_qtr", None)
        return d

    r_and_d_percent_last_qtr: float | None
    r_and_d_percent_last_qtr_formatted: str | None
    debt_percent_formatted: str | None
    new_ceo_date: str | None

    @property
    def new_ceo_date_dt(self) -> datetime.date | None:
        """Parsed new_ceo_date as a date object, or None if unavailable."""
        return parse_date(self.new_ceo_date)


@dataclass(frozen=True, slots=True)
class StockData(DataClassDictMixin):
    """Complete stock data response from the OtherMarketData query."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    symbol: str
    ratings: Ratings | None
    company: Company | None
    pricing: Pricing | None
    financials: Financials | None
    corporate_actions: CorporateActions | None
    industry: Industry | None
    ownership: BasicOwnership | None
    fundamentals: Fundamentals | None
    patterns: list[Pattern]

    def _str_header(self) -> str:
        """Format header line with symbol and company name."""
        company = self.company
        if company is not None and company.name is not None:
            return f"{self.symbol} - {company.name}"
        return self.symbol

    def _str_industry(self) -> str | None:
        """Format industry line, or None if no industry data."""
        industry = self.industry
        if industry is None or industry.name is None:
            return None
        rank_part = ""
        company = self.company
        if company is not None and company.industry_group_rank is not None:
            rank_part = f" (Rank #{company.industry_group_rank})"
        return f"Industry: {industry.name}{rank_part}"

    def _str_ratings(self) -> str | None:
        """Format ratings line, or None if no rating data."""
        r = self.ratings
        if r is None:
            return None
        parts = []
        if r.composite is not None:
            parts.append(f"Comp {r.composite}")
        if r.eps is not None:
            parts.append(f"EPS {r.eps}")
        if r.rs is not None:
            parts.append(f"RS {r.rs}")
        if r.smr is not None:
            parts.append(f"SMR {r.smr}")
        if r.ad is not None:
            parts.append(f"A/D {r.ad}")
        return f"Ratings: {' | '.join(parts)}" if parts else None

    def _str_pricing(self) -> str | None:
        """Format pricing line, or None if no pricing data."""
        pricing = self.pricing
        if pricing is None:
            return None
        parts = []
        if pricing.market_cap_formatted is not None:
            parts.append(f"Market Cap {pricing.market_cap_formatted}")
        if pricing.avg_dollar_volume_50d_formatted is not None:
            parts.append(f"50d Avg Vol {pricing.avg_dollar_volume_50d_formatted}")
        return f"Price: {' | '.join(parts)}" if parts else None

    def _str_financials(self) -> str | None:
        """Format financials line, or None if no financial data."""
        fin = self.financials
        if fin is None:
            return None
        parts = []
        if fin.eps_growth_rate is not None:
            parts.append(f"EPS Growth {fin.eps_growth_rate}%")
        if fin.sales_growth_rate_3y is not None:
            parts.append(f"Sales Growth {fin.sales_growth_rate_3y}%")
        return f"Financials: {' | '.join(parts)}" if parts else None

    def _str_pattern(self) -> str | None:
        """Format pattern line, or None if no patterns."""
        if not self.patterns:
            return None
        p = self.patterns[0]
        pat_parts = []
        if p.stage is not None:
            pat_parts.append(f"Stage {p.stage}")
        if p.pivot_price_formatted is not None:
            pat_parts.append(f"Pivot {p.pivot_price_formatted}")
        detail = f" ({', '.join(pat_parts)})" if pat_parts else ""
        return f"Pattern: {p.type or 'Unknown'}{detail}"

    def __str__(self) -> str:
        """Human-readable multi-line summary for LLM consumption."""
        lines = [
            self._str_header(),
            self._str_industry(),
            self._str_ratings(),
            self._str_pricing(),
            self._str_financials(),
            self._str_pattern(),
        ]
        return "\n".join(line for line in lines if line is not None)


@dataclass(frozen=True, slots=True)
class WatchlistEntry(DataClassDictMixin):
    """Single row from an AdhocScreen watchlist query."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    symbol: str | None
    company_name: str | None
    list_rank: int | None
    price: float | None
    price_net_change: float | None
    price_pct_change: float | None
    price_pct_off_52w_high: float | None
    volume: int | None
    volume_change: int | None
    volume_pct_change: float | None
    composite_rating: int | None
    eps_rating: int | None
    rs_rating: int | None
    acc_dis_rating: str | None
    smr_rating: str | None
    industry_group_rank: int | None
    industry_name: str | None

    def _str_header(self) -> str:
        """Format header line with symbol, name, and price."""
        sym = self.symbol or "N/A"
        name = self.company_name or "Unknown"
        price_str = f"${self.price:.2f}" if self.price is not None else "N/A"
        pct = (
            f" ({self.price_pct_change:+.1f}%)"
            if self.price_pct_change is not None
            else ""
        )
        return f"{sym} - {name} | Price: {price_str}{pct}"

    def _str_ratings(self) -> str | None:
        """Format ratings line, or None if no rating data."""
        parts = []
        if self.composite_rating is not None:
            parts.append(f"Comp {self.composite_rating}")
        if self.eps_rating is not None:
            parts.append(f"EPS {self.eps_rating}")
        if self.rs_rating is not None:
            parts.append(f"RS {self.rs_rating}")
        if self.smr_rating is not None:
            parts.append(f"SMR {self.smr_rating}")
        if self.acc_dis_rating is not None:
            parts.append(f"A/D {self.acc_dis_rating}")
        return f"Ratings: {' | '.join(parts)}" if parts else None

    def _str_industry(self) -> str | None:
        """Format industry line, or None if no industry data."""
        if self.industry_name is None:
            return None
        rank_part = ""
        if self.industry_group_rank is not None:
            rank_part = f" (Rank #{self.industry_group_rank})"
        return f"Industry: {self.industry_name}{rank_part}"

    def __str__(self) -> str:
        """Human-readable multi-line summary for LLM consumption."""
        lines = [
            self._str_header(),
            self._str_ratings(),
            self._str_industry(),
        ]
        return "\n".join(line for line in lines if line is not None)


@dataclass(frozen=True, slots=True)
class QuarterlyFundOwnership(DataClassDictMixin):
    """Fund ownership count for a single quarter."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    date: str | None
    count: str | None

    @property
    def date_dt(self) -> datetime.date | None:
        """Parsed date as a date object, or None if unavailable."""
        return parse_date(self.date)


@dataclass(frozen=True, slots=True)
class OwnershipData(DataClassDictMixin):
    """Complete ownership data response from the Ownership query."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    symbol: str
    funds_float_pct: str | None
    quarterly_funds: list[QuarterlyFundOwnership]


@dataclass(frozen=True, slots=True)
class WatchlistSummary(DataClassDictMixin):
    """Summary of a user watchlist (from GetAllWatchlistNames query)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    id: str | None
    name: str | None
    last_modified: str | None
    description: str | None

    @property
    def last_modified_dt(self) -> datetime.datetime | None:
        """Parsed last_modified as a datetime object, or None if unavailable."""
        return parse_datetime(self.last_modified)


@dataclass(frozen=True, slots=True)
class WatchlistSymbol(DataClassDictMixin):
    """Single symbol entry in a watchlist (from FlaggedSymbols query)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    key: str | None
    dow_jones_key: str | None


@dataclass(frozen=True, slots=True)
class WatchlistDetail(DataClassDictMixin):
    """Full watchlist with its symbol items (from FlaggedSymbols query)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    id: str | None
    name: str | None
    last_modified: str | None
    description: str | None
    items: list[WatchlistSymbol]

    @property
    def last_modified_dt(self) -> datetime.datetime | None:
        """Parsed last_modified as a datetime object, or None if unavailable."""
        return parse_datetime(self.last_modified)


@dataclass(frozen=True, slots=True)
class ScreenSource(DataClassDictMixin):
    """Data source linked to a saved screen."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    id: str | None
    type: str | None
    pub: str | None


@dataclass(frozen=True, slots=True)
class Screen(DataClassDictMixin):
    """A saved screen definition (from Screens query)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    id: str | None
    name: str | None
    type: str | None
    source: ScreenSource | None
    description: str | None
    filter_criteria: str | None
    created_at: str | None
    updated_at: str | None

    @property
    def created_at_dt(self) -> datetime.datetime | None:
        """Parsed created_at as a datetime object, or None if unavailable."""
        return parse_datetime(self.created_at)

    @property
    def updated_at_dt(self) -> datetime.datetime | None:
        """Parsed updated_at as a datetime object, or None if unavailable."""
        return parse_datetime(self.updated_at)


@dataclass(frozen=True, slots=True)
class ScreenResult(DataClassDictMixin):
    """Result of running a named screen via MarketDataScreen query.

    Rows contain dynamic columns that vary by screen_name. Each dict
    maps column name (e.g. "Symbol", "CompanyName") to its string value.
    """

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    screen_name: str | None
    elapsed_time: str | None
    num_instruments: int | None
    rows: list[dict[str, str | None]]


@dataclass(frozen=True, slots=True)
class DataPoint(DataClassDictMixin):
    """Single OHLCV data point from a time series."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    start_date_time: str
    end_date_time: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None  # API calls this "last" but we use standard OHLCV naming
    volume: float | None

    @property
    def start_date_time_dt(self) -> datetime.datetime | None:
        """Parsed start_date_time as a datetime object, or None if unavailable."""
        return parse_datetime(self.start_date_time)

    @property
    def end_date_time_dt(self) -> datetime.datetime | None:
        """Parsed end_date_time as a datetime object, or None if unavailable."""
        return parse_datetime(self.end_date_time)


@dataclass(frozen=True, slots=True)
class Quote(DataClassDictMixin):
    """Real-time or extended-hours quote data."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    trade_date_time: str | None
    timeliness: str | None
    quote_type: str | None
    last: float | None
    volume: float | None
    percent_change: float | None
    net_change: float | None

    @property
    def trade_date_time_dt(self) -> datetime.datetime | None:
        """Parsed trade_date_time as a datetime object, or None if unavailable."""
        return parse_datetime(self.trade_date_time)


@dataclass(frozen=True, slots=True)
class TimeSeries(DataClassDictMixin):
    """Time series container with period and data points."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    period: str
    data_points: list[DataPoint]


@dataclass(frozen=True, slots=True)
class ExchangeHoliday(DataClassDictMixin):
    """Exchange holiday entry."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    name: str
    holiday_type: str | None
    description: str | None
    start_date_time: str
    end_date_time: str

    @property
    def start_date_time_dt(self) -> datetime.datetime | None:
        """Parsed start_date_time as a datetime object, or None if unavailable."""
        return parse_datetime(self.start_date_time)

    @property
    def end_date_time_dt(self) -> datetime.datetime | None:
        """Parsed end_date_time as a datetime object, or None if unavailable."""
        return parse_datetime(self.end_date_time)


@dataclass(frozen=True, slots=True)
class ExchangeInfo(DataClassDictMixin):
    """Exchange metadata and holiday schedule."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    city: str | None
    country_code: str | None
    exchange_iso: str | None
    holidays: list[ExchangeHoliday]


@dataclass(frozen=True, slots=True)
class ChartData(DataClassDictMixin):
    """Complete chart data response from the ChartMarketData query."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    symbol: str
    time_series: TimeSeries | None
    quote: Quote | None
    premarket_quote: Quote | None
    postmarket_quote: Quote | None
    current_market_state: str | None
    exchange: ExchangeInfo | None

    def __str__(self) -> str:
        """Human-readable multi-line summary for LLM consumption."""
        lines: list[str] = [f"{self.symbol} Chart Data"]

        ts = self.time_series
        if ts is not None and ts.data_points:
            first = ts.data_points[0].start_date_time
            last = ts.data_points[-1].start_date_time
            lines.append(
                f"Date range: {first} to {last} | Points: {len(ts.data_points)}"
            )
        else:
            lines.append("No time series data")

        q = self.quote
        if q is not None and q.last is not None:
            vol_str = ""
            if q.volume is not None:
                vol_str = f" | Vol: {q.volume:,.0f}"
            lines.append(f"Latest: ${q.last}{vol_str}")

        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class ReportedPeriod(DataClassDictMixin):
    """Historical reported earnings or sales for a single annual period."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("formatted_value") is not None:
            d.pop("value", None)
        if d.get("formatted_pct_change") is not None:
            d.pop("pct_change_yoy", None)
        return d

    value: float | None
    formatted_value: str | None
    pct_change_yoy: float | None
    formatted_pct_change: str | None
    period_offset: str
    period_end_date: str | None

    @property
    def period_end_date_dt(self) -> datetime.date | None:
        """Parsed period_end_date as a date object, or None if unavailable."""
        return parse_date(self.period_end_date)


@dataclass(frozen=True, slots=True)
class EstimatePeriod(DataClassDictMixin):
    """Future EPS or sales estimate for a single annual period."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    def __post_serialize__(self, d: dict) -> dict:
        if d.get("formatted_value") is not None:
            d.pop("value", None)
        if d.get("formatted_pct_change") is not None:
            d.pop("pct_change_yoy", None)
        return d

    value: float | None
    formatted_value: str | None
    pct_change_yoy: float | None
    formatted_pct_change: str | None
    period_offset: str
    period: str | None
    revision_direction: str | None  # "UP", "DOWN", or None


@dataclass(frozen=True, slots=True)
class FundamentalData(DataClassDictMixin):
    """Fundamental financial data from the FundermentalDataBox query."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    symbol: str
    company_name: str | None
    reported_earnings: list[ReportedPeriod]
    reported_sales: list[ReportedPeriod]
    eps_estimates: list[EstimatePeriod]
    sales_estimates: list[EstimatePeriod]

    def __str__(self) -> str:
        """Human-readable multi-line summary for LLM consumption."""
        name_part = f" ({self.company_name})" if self.company_name else ""
        lines: list[str] = [f"{self.symbol} Fundamentals{name_part}"]

        if self.reported_earnings:
            latest = self.reported_earnings[0]
            eps_str = latest.formatted_value or "N/A"
            lines.append(
                f"Reported periods: {len(self.reported_earnings)}"
                f" | Latest EPS: {eps_str}"
            )
        else:
            lines.append("Reported earnings: No data")

        if self.eps_estimates:
            next_est = self.eps_estimates[0]
            est_str = next_est.formatted_value or "N/A"
            lines.append(
                f"Estimated periods: {len(self.eps_estimates)} | Next EPS: {est_str}"
            )
        else:
            lines.append("EPS estimates: No data")

        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class AlertInstrument(DataClassDictMixin):
    """Instrument details from an alert subscription or triggered alert."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    djid: str | None
    ticker: str | None
    charting_symbol: str | None


@dataclass(frozen=True, slots=True)
class AlertTerm(DataClassDictMixin):
    """Alert trigger criteria term (value/operator/field with optional instrument)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    value: str | None
    operator: str | None
    field: str | None
    instrument: AlertInstrument | None  # None for CompanyTermCriteria


@dataclass(frozen=True, slots=True)
class AlertCriteria(DataClassDictMixin):
    """Full alert criteria including type and trigger term."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    criteria_id: str
    engine: str | None
    product: str | None
    alert_type: str | None
    term: AlertTerm | None


@dataclass(frozen=True, slots=True)
class DeliveryPreference(DataClassDictMixin):
    """Alert delivery method and timing."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    method: str
    type: str


@dataclass(frozen=True, slots=True)
class AlertSubscription(DataClassDictMixin):
    """A single active alert subscription."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    delivery_preferences: list[DeliveryPreference]
    criteria: AlertCriteria | None
    create_date: str | None
    note: str | None

    @property
    def create_date_dt(self) -> datetime.datetime | None:
        """Parsed create_date as a datetime object, or None if unavailable."""
        return parse_datetime(self.create_date)


@dataclass(frozen=True, slots=True)
class AlertSubscriptionList(DataClassDictMixin):
    """Collection of active alert subscriptions with quota info."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    subscriptions: list[AlertSubscription]
    num_subscriptions: int
    remaining_subscriptions: int


@dataclass(frozen=True, slots=True)
class TriggeredAlertTerm(DataClassDictMixin):
    """Alert trigger criteria term from a triggered alert (includes dj_key)."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    value: str | None
    operator: str | None
    field: str | None
    dj_key: str | None
    instrument: AlertInstrument | None  # None for CompanyTermCriteria


@dataclass(frozen=True, slots=True)
class TriggeredAlert(DataClassDictMixin):
    """A single triggered/fired alert with its payload."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    alert_id: str
    alert_type: str | None
    engine: str | None
    delivery_preference: DeliveryPreference | None  # SINGULAR (not list)
    term: TriggeredAlertTerm | None
    criteria_id: str | None
    payload: dict[str, Any]  # Opaque JSON scalar -- do NOT parse
    product: str | None
    delivered: bool
    viewed: bool
    deleted: bool
    create_date: str | None
    ttl: int | None

    @property
    def create_date_dt(self) -> datetime.datetime | None:
        """Parsed create_date as a datetime object, or None if unavailable."""
        return parse_datetime(self.create_date)


@dataclass(frozen=True, slots=True)
class TriggeredAlertList(DataClassDictMixin):
    """Collection of triggered alerts with pagination cursor."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    cursor_id: str | None
    alerts: list[TriggeredAlert]


@dataclass(frozen=True, slots=True)
class LayoutColumn(DataClassDictMixin):
    """Single column in a market data layout."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    md_item_id: str
    name: str
    width: int | None
    locked: bool
    visible: bool


@dataclass(frozen=True, slots=True)
class Layout(DataClassDictMixin):
    """User-saved market data column layout."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    id: str
    name: str
    site: str | None
    columns: list[LayoutColumn]


@dataclass(frozen=True, slots=True)
class ChartMarkup(DataClassDictMixin):
    """User-saved chart markup/annotation."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    id: str
    name: str | None
    data: str  # Opaque serialized JSON — NOT parsed
    frequency: str | None
    site: str | None
    created_at: str | None
    updated_at: str | None

    @property
    def created_at_dt(self) -> datetime.datetime | None:
        """Parsed created_at as a datetime object, or None if unavailable."""
        return parse_datetime(self.created_at)

    @property
    def updated_at_dt(self) -> datetime.datetime | None:
        """Parsed updated_at as a datetime object, or None if unavailable."""
        return parse_datetime(self.updated_at)


@dataclass(frozen=True, slots=True)
class ChartMarkupList(DataClassDictMixin):
    """Paginated collection of chart markups."""

    class Config(BaseConfig):
        omit_none = True

    def to_json(self) -> str:
        """Serialize this dataclass to a JSON string."""
        return json.dumps(self.to_dict())

    cursor_id: str | None
    markups: list[ChartMarkup]
