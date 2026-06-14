import logging
from datetime import date

from backend.config import AppConfig
from backend.strategy.engine import StrategyEngine

logger = logging.getLogger(__name__)


def run_strategy_scoring(config: AppConfig) -> int:
    """Run the full three-layer strategy engine and persist recommendations.

    This job should be scheduled after daily_close (which syncs latest kline
    data into Parquet) so the engine always scores against fresh data.
    """
    engine = StrategyEngine(config)
    target_date = date.today()
    recommendations = engine.run(target_date=target_date)

    if not recommendations:
        logger.warning("Strategy scoring produced no recommendations")
        return 0

    low = sum(1 for r in recommendations if r.get("risk_level") == "low")
    med = sum(1 for r in recommendations if r.get("risk_level") == "medium")
    high = sum(1 for r in recommendations if r.get("risk_level") == "high")
    logger.info(
        f"Strategy scoring complete: {len(recommendations)} recommendations "
        f"(low={low}, medium={med}, high={high})"
    )
    return len(recommendations)
