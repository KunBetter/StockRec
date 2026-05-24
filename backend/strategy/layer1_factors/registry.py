from backend.strategy.layer1_factors.base_factor import BaseFactor
from backend.strategy.layer1_factors.value_factors import EPFactor, BPFactor, SPFactor, DividendYieldFactor
from backend.strategy.layer1_factors.quality_factors import ROEFactor, ROAFactor, GrossMarginFactor, AssetTurnoverFactor
from backend.strategy.layer1_factors.growth_factors import RevenueGrowthFactor, ProfitGrowthFactor, RdRatioFactor
from backend.strategy.layer1_factors.momentum_factors import Momentum1MFactor, Momentum3MFactor, Momentum12m1mFactor
from backend.strategy.layer1_factors.reversal_factors import WeeklyReversalFactor, IntradayReversalFactor
from backend.strategy.layer1_factors.volatility_factors import HistoricalVolatilityFactor, DownsideVolatilityFactor
from backend.strategy.layer1_factors.liquidity_factors import TurnoverFactor, AmihudIlliquidityFactor, TurnoverChangeFactor
from backend.strategy.layer1_factors.capital_flow_factors import MajorInflowFactor, NorthboundPctFactor, MarginChangeFactor


ALL_FACTORS: list[BaseFactor] = [
    EPFactor(),
    BPFactor(),
    SPFactor(),
    DividendYieldFactor(),
    ROEFactor(),
    ROAFactor(),
    GrossMarginFactor(),
    AssetTurnoverFactor(),
    RevenueGrowthFactor(),
    ProfitGrowthFactor(),
    RdRatioFactor(),
    Momentum1MFactor(),
    Momentum3MFactor(),
    Momentum12m1mFactor(),
    WeeklyReversalFactor(),
    IntradayReversalFactor(),
    HistoricalVolatilityFactor(),
    DownsideVolatilityFactor(),
    TurnoverFactor(),
    AmihudIlliquidityFactor(),
    TurnoverChangeFactor(),
    MajorInflowFactor(),
    NorthboundPctFactor(),
    MarginChangeFactor(),
]

FACTOR_REGISTRY: dict[str, BaseFactor] = {f.name: f for f in ALL_FACTORS}


def get_factor(name: str) -> BaseFactor:
    if name not in FACTOR_REGISTRY:
        raise KeyError(f"Factor {name} not registered. Available: {list(FACTOR_REGISTRY.keys())}")
    return FACTOR_REGISTRY[name]


def get_factors_by_category(category: str) -> list[BaseFactor]:
    return [f for f in ALL_FACTORS if f.category == category]


def get_all_factor_names() -> list[str]:
    return [f.name for f in ALL_FACTORS]
