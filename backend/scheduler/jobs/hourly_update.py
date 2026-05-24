import logging
from datetime import date

from backend.config import AppConfig
from backend.data.data_orchestrator import DataOrchestrator
from backend.persistence.database import get_session
from backend.persistence.repository import Repository
from backend.persistence.models import Stock, Recommendation

logger = logging.getLogger(__name__)


def run_hourly_update(config: AppConfig) -> int:
    session = get_session()
    try:
        stock_repo = Repository(session, Stock)
        stocks = stock_repo.find_by(status="active")
        if not stocks:
            logger.warning("No active stocks in database")
            return 0

        symbols = [s.symbol for s in stocks]
        orch = DataOrchestrator(config)

        df = orch.fetch_realtime_prices(symbols)
        if df.empty:
            logger.warning("No realtime data fetched")
            orch.cleanup()
            return 0

        rec_repo = Repository(session, Recommendation)
        today = date.today()
        updated = 0

        for _, row in df.iterrows():
            symbol = row.get("symbol")
            if not symbol:
                continue
            price = row.get("price")
            pct = row.get("pct_change")
            if price is None:
                continue

            existing = rec_repo.find_one_by(symbol=symbol, trade_date=today)
            if existing:
                existing.current_price = float(price)
                if pct is not None:
                    existing.price_change_pct = float(pct)
                updated += 1
            else:
                rec_repo.create(
                    symbol=symbol,
                    trade_date=today,
                    current_price=float(price),
                    price_change_pct=float(pct) if pct is not None else 0,
                )

        session.commit()
        orch.cleanup()
        logger.info(f"Hourly update: {updated} prices updated")
        return len(df)
    finally:
        session.close()
