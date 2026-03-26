"""GraphQL query strings and shared query payload pieces."""

from tickerscope.queries import load_query

OWNERSHIP_QUERY = load_query("ownership")
ADHOC_SCREEN_QUERY = load_query("adhoc_screen")
OTHER_MARKET_DATA_QUERY = load_query("other_market_data")
WATCHLIST_NAMES_QUERY = load_query("watchlist_names")
FLAGGED_SYMBOLS_QUERY = load_query("flagged_symbols")
SCREENS_QUERY = load_query("screens")
MARKET_DATA_SCREEN_QUERY = load_query("market_data_screen")
CHART_MARKET_DATA_QUERY = load_query("chart_market_data")
CHART_MARKET_DATA_WEEKLY_QUERY = load_query("chart_market_data_weekly")
FUNDAMENTALS_QUERY = load_query("fundamentals")
ACTIVE_ALERTS_QUERY = load_query("active_alerts")
TRIGGERED_ALERTS_QUERY = load_query("triggered_alerts")
MARKET_DATA_LAYOUTS_QUERY = load_query("market_data_layouts")
CHART_MARKUPS_QUERY = load_query("chart_markups")
RS_RATING_RI_PANEL_QUERY = load_query("rs_rating_ri_panel")
GET_SERVER_DATE_TIME_QUERY = load_query("get_server_date_time")
ALL_PANELS_QUERY = load_query("all_panels")
NAV_TREE_QUERY = load_query("nav_tree")
COACH_TREE_QUERY = load_query("coach_tree")

WATCHLIST_COLUMNS = [
    {"name": "Symbol"},
    {"name": "CompanyName"},
    {
        "name": "ListRank",
        "sortInformation": {"direction": "ASCENDING", "order": "PRIMARY"},
    },
    {"name": "Price"},
    {"name": "PriceNetChg"},
    {"name": "PricePctChg"},
    {"name": "PricePctOff52WHigh"},
    {"name": "VolumePctChgVs50DAvgVolume"},
    {"name": "VolumeAvg50Day"},
    {"name": "MarketCapIntraday"},
    {"name": "CompositeRating"},
    {"name": "EPSRating"},
    {"name": "RSRating"},
    {"name": "AccDisRating"},
    {"name": "SMRRating"},
    {"name": "IndustryGroupRank"},
    {"name": "IndustryName"},
    {"name": "VolumeDollarAvg50D"},
    {"name": "IPODate"},
    {"name": "DowJonesKey"},
    {"name": "ChartingSymbol"},
    {"name": "DowJonesInstrumentType"},
    {"name": "DowJonesInstrumentSubType"},
]
