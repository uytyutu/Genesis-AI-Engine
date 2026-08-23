"""Global market registry + factory for API Farm (no fake LIVE coverage)."""

from swarm.farm_channels.rapidapi.markets.factory import (
    market_capabilities_matrix,
    products_catalog,
    register_market,
)
from swarm.farm_channels.rapidapi.markets.quality import market_quality_score, wave_quality_table
from swarm.farm_channels.rapidapi.markets.registry import (
    MARKET_STATUS,
    GlobalMarketRegistry,
    coverage_summary,
    get_market,
    list_markets,
)

__all__ = [
    "MARKET_STATUS",
    "GlobalMarketRegistry",
    "coverage_summary",
    "get_market",
    "list_markets",
    "market_capabilities_matrix",
    "market_quality_score",
    "products_catalog",
    "register_market",
    "wave_quality_table",
]
