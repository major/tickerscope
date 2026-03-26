"""Typed dataclass models for TickerScope API responses."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any


from tickerscope._dates import parse_date, parse_date_list, parse_datetime
from tickerscope._serialization import SerializableDataclass


@dataclass(frozen=True, slots=True)
class Ratings(SerializableDataclass):
    """Stock composite, EPS, RS, SMR, and A/D ratings."""

    composite: int | None
    eps: int | None
    rs: int | None
    smr: str | None
    ad: str | None


@dataclass(frozen=True, slots=True)
class Company(SerializableDataclass):
    """Company profile information."""

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
    city: str | None = None
    country: str | None = None
    state_province: str | None = None
    instrument_sub_type: str | None = None

    @property
    def ipo_date_dt(self) -> datetime.date | None:
        """Parsed ipo_date as a date object, or None if unavailable."""
        return parse_date(self.ipo_date)


@dataclass(frozen=True, slots=True)
class PricePercentChanges(SerializableDataclass):
    """Price percent changes vs various reference periods."""

    ytd: float | None
    mtd: float | None
    qtd: float | None
    wtd: float | None
    vs_1d: float | None
    vs_1m: float | None
    vs_3m: float | None
    vs_year_high: float | None
    vs_year_low: float | None
    vs_5d: float | None = None
    vs_sp500_26w: float | None = None
    vs_ma10d: float | None = None
    vs_ma21d: float | None = None
    vs_ma50d: float | None = None
    vs_ma150d: float | None = None
    vs_ma200d: float | None = None


@dataclass(frozen=True, slots=True)
class Pricing(SerializableDataclass):
    """Pricing statistics and market data."""

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
    ant_dates: list[str | None]
    price_percent_changes: PricePercentChanges | None
    volume_percent_change_vs_50d: float | None
    historical_price_statistics: list[HistoricalPriceStatistic] | None = None
    volume_moving_averages: list[VolumeMovingAverage] | None = None
    volume_percent_change_vs_6m: float | None = None
    volume_percent_change_vs_10w: float | None = None
    dividend_yield: float | None = None
    dividend_yield_formatted: str | None = None
    price_to_cash_flow_ratio: float | None = None
    price_to_cash_flow_ratio_formatted: str | None = None
    forward_price_to_earnings_ratio: float | None = None
    forward_price_to_earnings_ratio_formatted: str | None = None
    price_to_sales_ratio: float | None = None
    price_to_sales_ratio_formatted: str | None = None
    price_to_earnings_ratio: float | None = None
    price_to_earnings_ratio_formatted: str | None = None
    pe_vs_sp500: float | None = None
    pe_vs_sp500_formatted: str | None = None
    alpha: float | None = None
    alpha_formatted: str | None = None
    beta: float | None = None
    beta_formatted: str | None = None
    short_interest_days_to_cover: float | None = None
    short_interest_days_to_cover_formatted: str | None = None
    short_interest_days_to_cover_pct_change: float | None = None
    short_interest_days_to_cover_pct_change_formatted: str | None = None
    short_interest_volume: int | None = None
    short_interest_volume_formatted: str | None = None
    is_daily_blue_dot_event: bool | None = None
    is_weekly_blue_dot_event: bool | None = None
    pricing_start_date: str | None = None
    pricing_end_date: str | None = None

    @property
    def blue_dot_daily_dates_dt(self) -> list[datetime.date | None]:
        """Parsed blue_dot_daily_dates as a list of date objects."""
        return parse_date_list(self.blue_dot_daily_dates)

    @property
    def blue_dot_weekly_dates_dt(self) -> list[datetime.date | None]:
        """Parsed blue_dot_weekly_dates as a list of date objects."""
        return parse_date_list(self.blue_dot_weekly_dates)

    @property
    def ant_dates_dt(self) -> list[datetime.date | None]:
        """Parsed ant_dates as a list of date objects."""
        return parse_date_list(self.ant_dates)

    @property
    def pricing_start_date_dt(self) -> datetime.date | None:
        return parse_date(self.pricing_start_date)

    @property
    def pricing_end_date_dt(self) -> datetime.date | None:
        return parse_date(self.pricing_end_date)


@dataclass(frozen=True, slots=True)
class Financials(SerializableDataclass):
    """Financial metrics and earnings data."""

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
    cash_flow_per_share: float | None = None
    cash_flow_per_share_formatted: str | None = None

    @property
    def eps_due_date_dt(self) -> datetime.date | None:
        """Parsed eps_due_date as a date object, or None if unavailable."""
        return parse_date(self.eps_due_date)

    @property
    def eps_last_reported_date_dt(self) -> datetime.date | None:
        """Parsed eps_last_reported_date as a date object, or None if unavailable."""
        return parse_date(self.eps_last_reported_date)


@dataclass(frozen=True, slots=True)
class Dividend(SerializableDataclass):
    """Individual dividend event."""

    ex_date: str | None
    amount: str | None
    change_indicator: str | None

    @property
    def ex_date_dt(self) -> datetime.date | None:
        """Parsed ex_date as a date object, or None if unavailable."""
        return parse_date(self.ex_date)


@dataclass(frozen=True, slots=True)
class CorporateActions(SerializableDataclass):
    """Corporate action history (dividends, splits, spinoffs)."""

    next_ex_dividend_date: str | None
    dividends: list[Dividend]
    splits: list[str | None]
    spinoffs: list[
        Any
    ]  # Element structure unknown; API always returns empty list in observed responses

    @property
    def next_ex_dividend_date_dt(self) -> datetime.date | None:
        """Parsed next_ex_dividend_date as a date object, or None if unavailable."""
        return parse_date(self.next_ex_dividend_date)


@dataclass(frozen=True, slots=True)
class TightArea(SerializableDataclass):
    """Tight price consolidation area on a chart (e.g. 3-weeks-tight)."""

    pattern_id: int | None
    start_date: str | None
    end_date: str | None
    length: int | None

    @property
    def start_date_dt(self) -> datetime.date | None:
        """Parsed start_date as a date object, or None if unavailable."""
        return parse_date(self.start_date)

    @property
    def end_date_dt(self) -> datetime.date | None:
        """Parsed end_date as a date object, or None if unavailable."""
        return parse_date(self.end_date)


@dataclass(frozen=True, slots=True)
class Pattern(SerializableDataclass):
    """Base class for all technical chart patterns detected by MarketSurge.

    Consolidation and Flat Base patterns use this class directly.
    Cup/saucer, double bottom, ascending base, and IPO base patterns
    use specialized subclasses with additional fields.
    """

    # Identity
    id: str | None
    pattern_type: str | None
    periodicity: str | None

    # Base characteristics
    base_stage: str | None
    base_number: int | None
    base_status: str | None
    base_length: int | None
    base_depth: float | None
    base_depth_formatted: str | None

    # Key dates
    base_start_date: str | None
    base_end_date: str | None
    base_bottom_date: str | None
    left_side_high_date: str | None

    # Pivot info
    pivot_price: float | None
    pivot_price_formatted: str | None
    pivot_date: str | None
    pivot_price_date: str | None

    # Performance on pivot day
    avg_volume_rate_pct_on_pivot: float | None
    avg_volume_rate_pct_on_pivot_formatted: str | None
    price_pct_change_on_pivot: float | None
    price_pct_change_on_pivot_formatted: str | None

    @property
    def pivot_date_dt(self) -> datetime.date | None:
        """Parsed pivot_date as a date object, or None if unavailable."""
        return parse_date(self.pivot_date)

    @property
    def pivot_price_date_dt(self) -> datetime.date | None:
        """Parsed pivot_price_date as a date object, or None if unavailable."""
        return parse_date(self.pivot_price_date)

    @property
    def base_start_date_dt(self) -> datetime.date | None:
        """Parsed base_start_date as a date object, or None if unavailable."""
        return parse_date(self.base_start_date)

    @property
    def base_end_date_dt(self) -> datetime.date | None:
        """Parsed base_end_date as a date object, or None if unavailable."""
        return parse_date(self.base_end_date)

    @property
    def base_bottom_date_dt(self) -> datetime.date | None:
        """Parsed base_bottom_date as a date object, or None if unavailable."""
        return parse_date(self.base_bottom_date)

    @property
    def left_side_high_date_dt(self) -> datetime.date | None:
        """Parsed left_side_high_date as a date object, or None if unavailable."""
        return parse_date(self.left_side_high_date)


@dataclass(frozen=True, slots=True)
class CupPattern(Pattern):
    """Cup or saucer pattern, with or without handle.

    Covers CUP_WITH_HANDLE, CUP_WITHOUT_HANDLE, SAUCER_WITH_HANDLE,
    and SAUCER_WITHOUT_HANDLE pattern types.
    """

    handle_depth: float | None
    handle_depth_formatted: str | None
    handle_length: int | None
    cup_length: int | None
    cup_end_date: str | None
    handle_low_date: str | None
    handle_start_date: str | None

    @property
    def cup_end_date_dt(self) -> datetime.date | None:
        """Parsed cup_end_date as a date object, or None if unavailable."""
        return parse_date(self.cup_end_date)

    @property
    def handle_low_date_dt(self) -> datetime.date | None:
        """Parsed handle_low_date as a date object, or None if unavailable."""
        return parse_date(self.handle_low_date)

    @property
    def handle_start_date_dt(self) -> datetime.date | None:
        """Parsed handle_start_date as a date object, or None if unavailable."""
        return parse_date(self.handle_start_date)


@dataclass(frozen=True, slots=True)
class DoubleBottomPattern(Pattern):
    """Double bottom (W-shaped) chart pattern."""

    first_bottom_date: str | None
    second_bottom_date: str | None
    mid_peak_date: str | None

    @property
    def first_bottom_date_dt(self) -> datetime.date | None:
        """Parsed first_bottom_date as a date object, or None if unavailable."""
        return parse_date(self.first_bottom_date)

    @property
    def second_bottom_date_dt(self) -> datetime.date | None:
        """Parsed second_bottom_date as a date object, or None if unavailable."""
        return parse_date(self.second_bottom_date)

    @property
    def mid_peak_date_dt(self) -> datetime.date | None:
        """Parsed mid_peak_date as a date object, or None if unavailable."""
        return parse_date(self.mid_peak_date)


@dataclass(frozen=True, slots=True)
class AscendingBasePattern(Pattern):
    """Ascending base pattern with three progressively higher pullbacks."""

    first_bottom_date: str | None
    second_ascending_high_date: str | None
    second_bottom_date: str | None
    third_ascending_high_date: str | None
    third_bottom_date: str | None
    pull_back_1_depth: float | None
    pull_back_1_depth_formatted: str | None
    pull_back_2_depth: float | None
    pull_back_2_depth_formatted: str | None
    pull_back_3_depth: float | None
    pull_back_3_depth_formatted: str | None

    @property
    def first_bottom_date_dt(self) -> datetime.date | None:
        """Parsed first_bottom_date as a date object, or None if unavailable."""
        return parse_date(self.first_bottom_date)

    @property
    def second_ascending_high_date_dt(self) -> datetime.date | None:
        """Parsed second_ascending_high_date as a date object, or None."""
        return parse_date(self.second_ascending_high_date)

    @property
    def second_bottom_date_dt(self) -> datetime.date | None:
        """Parsed second_bottom_date as a date object, or None if unavailable."""
        return parse_date(self.second_bottom_date)

    @property
    def third_ascending_high_date_dt(self) -> datetime.date | None:
        """Parsed third_ascending_high_date as a date object, or None."""
        return parse_date(self.third_ascending_high_date)

    @property
    def third_bottom_date_dt(self) -> datetime.date | None:
        """Parsed third_bottom_date as a date object, or None if unavailable."""
        return parse_date(self.third_bottom_date)


@dataclass(frozen=True, slots=True)
class IpoBasePattern(Pattern):
    """First base pattern after an IPO, with detailed bar and volume analysis."""

    up_bars: int | None
    blue_bars: int | None
    stall_bars: int | None
    down_bars: int | None
    red_bars: int | None
    support_bars: int | None
    up_volume_total: float | None
    up_volume_total_formatted: str | None
    down_volume_total: float | None
    down_volume_total_formatted: str | None
    volume_pct_change_on_pivot: float | None
    volume_pct_change_on_pivot_formatted: str | None


@dataclass(frozen=True, slots=True)
class HistoricalPriceStatistic(SerializableDataclass):
    """A single period of historical price statistics (high/low/close)."""

    period: str | None = None
    period_offset: str | None = None
    period_end_date: str | None = None
    price_high_date: str | None = None
    price_high: float | None = None
    price_low_date: str | None = None
    price_low: float | None = None
    price_close: float | None = None
    price_percent_change: float | None = None

    @property
    def period_end_date_dt(self) -> datetime.date | None:
        """Parsed period_end_date as a date object."""
        return parse_date(self.period_end_date)

    @property
    def price_high_date_dt(self) -> datetime.date | None:
        """Parsed price_high_date as a date object."""
        return parse_date(self.price_high_date)

    @property
    def price_low_date_dt(self) -> datetime.date | None:
        """Parsed price_low_date as a date object."""
        return parse_date(self.price_low_date)


@dataclass(frozen=True, slots=True)
class IndustryGroupSnapshot(SerializableDataclass):
    """A single time snapshot of industry group rank or relative strength."""

    period_offset: str
    value: int | None = None
    letter_value: str | None = None


@dataclass(frozen=True, slots=True)
class VolumeMovingAverage(SerializableDataclass):
    """A single volume moving average with period metadata."""

    value: float | None = None
    period: str | None = None
    period_offset: str | None = None


@dataclass(frozen=True, slots=True)
class Industry(SerializableDataclass):
    """Industry group information."""

    name: str | None
    sector: str | None
    code: str | None
    number_of_stocks: int | None
    group_rank_history: list[IndustryGroupSnapshot] | None = None
    group_rs_history: list[IndustryGroupSnapshot] | None = None


@dataclass(frozen=True, slots=True)
class BasicOwnership(SerializableDataclass):
    """Basic fund ownership metrics (from stock data query)."""

    funds_float_pct: float | None
    funds_float_pct_formatted: str | None


@dataclass(frozen=True, slots=True)
class Fundamentals(SerializableDataclass):
    """Fundamental financial data."""

    r_and_d_percent_last_qtr: float | None
    r_and_d_percent_last_qtr_formatted: str | None
    debt_percent_formatted: str | None
    new_ceo_date: str | None

    @property
    def new_ceo_date_dt(self) -> datetime.date | None:
        """Parsed new_ceo_date as a date object, or None if unavailable."""
        return parse_date(self.new_ceo_date)


@dataclass(frozen=True, slots=True)
class QuarterlyReportedPeriod(SerializableDataclass):
    """A single quarter of reported earnings or sales.

    Extracted from the OtherMarketData query's consensusFinancials section.
    Includes earnings surprise data and fiscal quarter identification.
    """

    value: float | None
    pct_change_yoy: float | None
    period_offset: str
    period_end_date: str | None
    effective_date: str | None
    percent_surprise: float | None
    surprise_amount: float | None
    quarter_number: int | None
    fiscal_year: int | None
    period: str | None = None

    @property
    def period_end_date_dt(self) -> datetime.date | None:
        """Parsed period_end_date as a date object, or None if unavailable."""
        return parse_date(self.period_end_date)

    @property
    def effective_date_dt(self) -> datetime.date | None:
        """Parsed effective_date as a date object, or None if unavailable."""
        return parse_date(self.effective_date)


@dataclass(frozen=True, slots=True)
class QuarterlyEstimate(SerializableDataclass):
    """A single quarter of estimated EPS or sales.

    Extracted from the OtherMarketData query's estimates section.
    Forward-looking analyst consensus estimates with revision direction.
    """

    value: float | None
    pct_change_yoy: float | None
    period_end_date: str | None
    effective_date: str | None
    revision_direction: str | None
    estimate_type: str | None

    @property
    def period_end_date_dt(self) -> datetime.date | None:
        """Parsed period_end_date as a date object, or None if unavailable."""
        return parse_date(self.period_end_date)

    @property
    def effective_date_dt(self) -> datetime.date | None:
        """Parsed effective_date as a date object, or None if unavailable."""
        return parse_date(self.effective_date)


@dataclass(frozen=True, slots=True)
class QuarterlyProfitMargin(SerializableDataclass):
    """Profit margin data for a single quarter.

    Extracted from the OtherMarketData query's profitMarginValues array.
    """

    period_offset: str
    period_end_date: str | None
    pre_tax_margin: float | None
    after_tax_margin: float | None
    gross_margin: float | None
    return_on_equity: float | None

    @property
    def period_end_date_dt(self) -> datetime.date | None:
        """Parsed period_end_date as a date object, or None if unavailable."""
        return parse_date(self.period_end_date)


@dataclass(frozen=True, slots=True)
class QuarterlyFinancials(SerializableDataclass):
    """Quarterly earnings, sales, estimates, and margins.

    Container for all quarterly financial data extracted from the
    OtherMarketData query. Up to 24 quarters of reported data and
    4 quarters of forward estimates.
    """

    reported_earnings: list[QuarterlyReportedPeriod]
    reported_sales: list[QuarterlyReportedPeriod]
    eps_estimates: list[QuarterlyEstimate]
    sales_estimates: list[QuarterlyEstimate]
    profit_margins: list[QuarterlyProfitMargin]


@dataclass(frozen=True, slots=True)
class StockData(SerializableDataclass):
    """Complete stock data response from the OtherMarketData query."""

    symbol: str
    ratings: Ratings | None
    company: Company | None
    pricing: Pricing | None
    financials: Financials | None
    corporate_actions: CorporateActions | None
    industry: Industry | None
    ownership: BasicOwnership | None
    fundamentals: Fundamentals | None
    quarterly_financials: QuarterlyFinancials | None
    patterns: list[Pattern]
    tight_areas: list[TightArea]

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
        if p.base_stage is not None:
            pat_parts.append(f"Stage {p.base_stage}")
        if p.pivot_price_formatted is not None:
            pat_parts.append(f"Pivot {p.pivot_price_formatted}")
        detail = f" ({', '.join(pat_parts)})" if pat_parts else ""
        return f"Pattern: {p.pattern_type or 'Unknown'}{detail}"

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
class WatchlistEntry(SerializableDataclass):
    """Single row from an AdhocScreen watchlist query."""

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
    market_cap: float | None = None
    volume_dollar_avg_50d: float | None = None
    ipo_date: str | None = None
    dow_jones_key: str | None = None
    charting_symbol: str | None = None
    instrument_type: str | None = None
    instrument_sub_type: str | None = None

    @property
    def ipo_date_dt(self) -> datetime.date | None:
        """Parsed ipo_date as a date object."""
        return parse_date(self.ipo_date)

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
class QuarterlyFundOwnership(SerializableDataclass):
    """Fund ownership count for a single quarter."""

    date: str | None
    count: str | None

    @property
    def date_dt(self) -> datetime.date | None:
        """Parsed date as a date object, or None if unavailable."""
        return parse_date(self.date)


@dataclass(frozen=True, slots=True)
class OwnershipData(SerializableDataclass):
    """Complete ownership data response from the Ownership query."""

    symbol: str
    funds_float_pct: str | None
    quarterly_funds: list[QuarterlyFundOwnership]


@dataclass(frozen=True, slots=True)
class RSRatingSnapshot(SerializableDataclass):
    """Single RS rating value at a specific period and time offset."""

    letter_value: str | None
    period: str | None
    period_offset: str | None
    value: int | None


@dataclass(frozen=True, slots=True)
class RSRatingHistory(SerializableDataclass):
    """RS rating history from RSRatingRIPanel query."""

    symbol: str
    ratings: list[RSRatingSnapshot]
    rs_line_new_high: bool | None


@dataclass(frozen=True, slots=True)
class WatchlistSummary(SerializableDataclass):
    """Summary of a user watchlist (from GetAllWatchlistNames query)."""

    id: int | None
    name: str | None
    last_modified: str | None
    description: str | None

    @property
    def last_modified_dt(self) -> datetime.datetime | None:
        """Parsed last_modified as a datetime object, or None if unavailable."""
        return parse_datetime(self.last_modified)


@dataclass(frozen=True, slots=True)
class WatchlistSymbol(SerializableDataclass):
    """Single symbol entry in a watchlist (from FlaggedSymbols query)."""

    key: str | None
    dow_jones_key: str | None


@dataclass(frozen=True, slots=True)
class WatchlistDetail(SerializableDataclass):
    """Full watchlist with its symbol items (from FlaggedSymbols query)."""

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
class ScreenSource(SerializableDataclass):
    """Data source linked to a saved screen."""

    id: str | None
    type: str | None
    pub: str | None


@dataclass(frozen=True, slots=True)
class Screen(SerializableDataclass):
    """A saved screen definition (from Screens query)."""

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
class ScreenResult(SerializableDataclass):
    """Result of running a named screen via MarketDataScreen query.

    Rows contain dynamic columns that vary by screen_name. Each dict
    maps column name (e.g. "Symbol", "CompanyName") to its string value.
    """

    screen_name: str | None
    elapsed_time: str | None
    num_instruments: int | None
    rows: list[dict[str, str | None]]


@dataclass(frozen=True, slots=True)
class Panel(SerializableDataclass):
    """A user panel configuration (from AllPanels query)."""

    id: str | None
    name: str | None
    site: str | None
    panel_type: str | None
    data: dict[str, Any] | None
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
class NavTreeNode(SerializableDataclass):
    """Base class for sidebar navigation tree nodes.

    Shared by NavTree and CoachTree queries. Folders and leaves
    extend this with type-specific fields.
    """

    id: str | None
    name: str | None
    parent_id: str | None
    node_type: str | None
    tree_type: str | None


@dataclass(frozen=True, slots=True)
class NavTreeFolder(NavTreeNode):
    """Folder node in the navigation tree, containing child nodes."""

    children: list[NavTreeNode]
    content_type: str | None


@dataclass(frozen=True, slots=True)
class NavTreeLeaf(NavTreeNode):
    """Leaf node in the navigation tree (watchlist, screen, or report)."""

    url: str | None
    reference_id: str | None
    reference_watchlist_id: str | None
    reference_screen_id: str | None
    reference_original_id: int | None = None


@dataclass(frozen=True, slots=True)
class CoachTreeData(SerializableDataclass):
    """IBD curated watchlists and screens from the CoachTree query.

    Contains two separate tree lists: one for watchlists and one for screens.
    Both reuse the NavTreeNode hierarchy (NavTreeFolder/NavTreeLeaf).
    """

    watchlists: list[NavTreeNode]
    screens: list[NavTreeNode]


@dataclass(frozen=True, slots=True)
class ReportInfo(SerializableDataclass):
    """Predefined MarketSurge report metadata.

    Reports (like "Bases Forming", "RS Line Blue Dot") are predefined stock
    lists identified by integer IDs. Use PREDEFINED_REPORTS for the full
    catalog.
    """

    name: str
    original_id: int


PREDEFINED_REPORTS: tuple[ReportInfo, ...] = (
    ReportInfo(name="Top 150 EPS Rating Stocks", original_id=1),
    ReportInfo(name="Top 150 RS Rating Stocks", original_id=3),
    ReportInfo(name="Fastest Growing Companies - Top 150", original_id=5),
    ReportInfo(name="Top 30 EPS Rating Stocks with High Avg. Volume", original_id=26),
    ReportInfo(name="Top 30 RS Rating Stocks with High Avg. Volume", original_id=27),
    ReportInfo(name="Weekly New High Report", original_id=28),
    ReportInfo(
        name="Weekly Report of Stocks Approaching or at New High", original_id=29
    ),
    ReportInfo(name="IBD 85-85 Index", original_id=39),
    ReportInfo(name="IBD Big Cap 20", original_id=40),
    ReportInfo(name="Today's Industry Performance: NEW HIGHS", original_id=47),
    ReportInfo(name="Today's Industry Performance: NEW LOWS", original_id=48),
    ReportInfo(name="Top 25 Funds over 10 Years", original_id=50),
    ReportInfo(name="Top 25 Industry or Sector Funds Over 3 Years", original_id=51),
    ReportInfo(name="Extended Stocks", original_id=84),
    ReportInfo(name="Accelerating Leaders", original_id=85),
    ReportInfo(name="Decelerating Leaders", original_id=87),
    ReportInfo(name="Top Rated Stocks", original_id=88),
    ReportInfo(name="MarketSurge Growth 250", original_id=93),
    ReportInfo(name="Additions", original_id=94),
    ReportInfo(name="Deletions", original_id=95),
    ReportInfo(name="IPO 1 Year", original_id=96),
    ReportInfo(name="RS Line New High", original_id=97),
    ReportInfo(name="Large Cap", original_id=98),
    ReportInfo(name="Mid Cap", original_id=99),
    ReportInfo(name="Small Cap", original_id=100),
    ReportInfo(name="Technical Strength", original_id=101),
    ReportInfo(name="Fundamental Strength", original_id=102),
    ReportInfo(name="Breaking Out Today", original_id=104),
    ReportInfo(name="Recent Breakouts", original_id=105),
    ReportInfo(name="Near Pivot", original_id=106),
    ReportInfo(name="Tight Areas", original_id=107),
    ReportInfo(name="Power from Pivot", original_id=108),
    ReportInfo(name="Breakaway Gap", original_id=109),
    ReportInfo(name="Earnings - Gap Up", original_id=110),
    ReportInfo(name="Earnings - Gap Down", original_id=111),
    ReportInfo(name="Earnings - Reported", original_id=112),
    ReportInfo(name="Earnings - Upcoming", original_id=113),
    ReportInfo(name="50-Day Break on Volume", original_id=114),
    ReportInfo(name="Pullback to 10-week Line", original_id=115),
    ReportInfo(name="Minervini Trend - 1 Month", original_id=119),
    ReportInfo(name="Minervini Trend - 5 Months", original_id=120),
    ReportInfo(name="RS Line Blue Dot", original_id=121),
    ReportInfo(name="Minervini Trend - 5 Months Wide", original_id=123),
    ReportInfo(name="Bases Forming", original_id=124),
    ReportInfo(name="All Tight Areas", original_id=125),
    ReportInfo(name="All RS Line New High", original_id=126),
    ReportInfo(name="Minervini Trend - 1 - 4 Months", original_id=127),
    ReportInfo(name="Barron's 400", original_id=130),
    ReportInfo(name="Ants List", original_id=131),
)
"""Full catalog of predefined MarketSurge reports.

Sourced from the MarketSurge frontend. These reports can be run via
``run_report(original_id)`` regardless of whether the user has pinned
them to their navigation sidebar.
"""


@dataclass(frozen=True, slots=True)
class AdhocScreenResult(SerializableDataclass):
    """Result of running an adhoc screen via MarketDataAdhocScreen query.

    Contains entries (WatchlistEntry items) and optional error values from the response.
    """

    entries: list[WatchlistEntry]
    error_values: list[str] | None


@dataclass(frozen=True, slots=True)
class DataPoint(SerializableDataclass):
    """Single OHLCV data point from a time series."""

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
class Quote(SerializableDataclass):
    """Real-time or extended-hours quote data."""

    trade_date_time: str | None
    timeliness: str | None
    quote_type: str | None
    last: float | None
    volume: float | None
    percent_change: float | None
    net_change: float | None
    last_formatted: str | None = None
    volume_formatted: str | None = None
    percent_change_formatted: str | None = None
    net_change_formatted: str | None = None

    @property
    def trade_date_time_dt(self) -> datetime.datetime | None:
        """Parsed trade_date_time as a datetime object, or None if unavailable."""
        return parse_datetime(self.trade_date_time)

    @property
    def close(self) -> float | None:
        """Price alias for `last` using standard OHLCV field naming (see DataPoint.close)."""
        return self.last


@dataclass(frozen=True, slots=True)
class TimeSeries(SerializableDataclass):
    """Time series container with period and data points."""

    period: str
    data_points: list[DataPoint]


@dataclass(frozen=True, slots=True)
class ExchangeHoliday(SerializableDataclass):
    """Exchange holiday entry."""

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
class ExchangeInfo(SerializableDataclass):
    """Exchange metadata and holiday schedule."""

    city: str | None
    country_code: str | None
    exchange_iso: str | None
    holidays: list[ExchangeHoliday]


@dataclass(frozen=True, slots=True)
class ChartData(SerializableDataclass):
    """Complete chart data response from the ChartMarketData query."""

    symbol: str
    time_series: TimeSeries | None
    benchmark_time_series: TimeSeries | None
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
class ReportedPeriod(SerializableDataclass):
    """Historical reported earnings or sales for a single annual period."""

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
class EstimatePeriod(SerializableDataclass):
    """Future EPS or sales estimate for a single annual period."""

    value: float | None
    formatted_value: str | None
    pct_change_yoy: float | None
    formatted_pct_change: str | None
    period_offset: str
    period: str | None
    revision_direction: str | None  # "UP", "DOWN", or None


@dataclass(frozen=True, slots=True)
class FundamentalData(SerializableDataclass):
    """Fundamental financial data from the FundermentalDataBox query."""

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
class StockAnalysis(SerializableDataclass):
    """Combined stock, fundamentals, and ownership data with partial failures."""

    symbol: str
    stock: StockData
    fundamentals: FundamentalData | None
    ownership: OwnershipData | None
    errors: list[str]


@dataclass(frozen=True, slots=True)
class AlertInstrument(SerializableDataclass):
    """Instrument details from an alert subscription or triggered alert."""

    djid: str | None
    ticker: str | None
    charting_symbol: str | None


@dataclass(frozen=True, slots=True)
class AlertTerm(SerializableDataclass):
    """Alert trigger criteria term (value/operator/field with optional instrument)."""

    value: str | None
    operator: str | None
    field: str | None
    instrument: AlertInstrument | None  # None for CompanyTermCriteria


@dataclass(frozen=True, slots=True)
class AlertCriteria(SerializableDataclass):
    """Full alert criteria including type and trigger term."""

    criteria_id: str
    engine: str | None
    product: str | None
    alert_type: str | None
    term: AlertTerm | None


@dataclass(frozen=True, slots=True)
class DeliveryPreference(SerializableDataclass):
    """Alert delivery method and timing."""

    method: str
    type: str


@dataclass(frozen=True, slots=True)
class AlertSubscription(SerializableDataclass):
    """A single active alert subscription."""

    delivery_preferences: list[DeliveryPreference]
    criteria: AlertCriteria | None
    create_date: str | None
    note: str | None

    @property
    def create_date_dt(self) -> datetime.datetime | None:
        """Parsed create_date as a datetime object, or None if unavailable."""
        return parse_datetime(self.create_date)


@dataclass(frozen=True, slots=True)
class AlertSubscriptionList(SerializableDataclass):
    """Collection of active alert subscriptions with quota info."""

    subscriptions: list[AlertSubscription]
    num_subscriptions: int
    remaining_subscriptions: int


@dataclass(frozen=True, slots=True)
class TriggeredAlertTerm(SerializableDataclass):
    """Alert trigger criteria term from a triggered alert (includes dj_key)."""

    value: str | None
    operator: str | None
    field: str | None
    dj_key: str | None
    instrument: AlertInstrument | None  # None for CompanyTermCriteria


@dataclass(frozen=True, slots=True)
class TriggeredAlert(SerializableDataclass):
    """A single triggered/fired alert with its payload."""

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
class TriggeredAlertList(SerializableDataclass):
    """Collection of triggered alerts with pagination cursor."""

    cursor_id: str | None
    alerts: list[TriggeredAlert]


@dataclass(frozen=True, slots=True)
class LayoutColumn(SerializableDataclass):
    """Single column in a market data layout."""

    md_item_id: str
    name: str
    width: int | None
    locked: bool
    visible: bool


@dataclass(frozen=True, slots=True)
class Layout(SerializableDataclass):
    """User-saved market data column layout."""

    id: str
    name: str
    site: str | None
    columns: list[LayoutColumn]


@dataclass(frozen=True, slots=True)
class ChartMarkup(SerializableDataclass):
    """User-saved chart markup/annotation."""

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
class ChartMarkupList(SerializableDataclass):
    """Paginated collection of chart markups."""

    cursor_id: str | None
    markups: list[ChartMarkup]
