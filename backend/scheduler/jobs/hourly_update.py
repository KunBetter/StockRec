import logging
import json
from datetime import date, datetime

from backend.config import AppConfig
from backend.data.data_orchestrator import DataOrchestrator
from backend.persistence.database import get_session
from backend.persistence.models import Stock, Recommendation
from backend.persistence.redis_client import cache_set_json, cache_get_json

logger = logging.getLogger(__name__)

REALTIME_CACHE_KEY = "realtime:prices"
REALTIME_CACHE_TTL = 60


def run_hourly_update(config: AppConfig) -> int:
    session = get_session()
    try:
        stocks = session.query(Stock).filter(Stock.status == "active").all()
        if not stocks:
            logger.warning("No active stocks in database")
            return 0

        symbols = [s.symbol for s in stocks]
        orch = DataOrchestrator(config)
        df = orch.fetch_realtime_prices(symbols)
        orch.cleanup()

        if df.empty:
            logger.warning("No realtime data fetched")
            return 0

        today = date.today()
        now = datetime.utcnow()
        updated = 0

        price_data = {}
        for _, row in df.iterrows():
            symbol = row.get("symbol")
            if not symbol:
                continue
            price = row.get("price")
            pct = row.get("pct_change")
            if price is None:
                continue

            price_data[symbol] = {"price": float(price), "pct_change": float(pct) if pct is not None else 0, "updated": now.isoformat()}

            stock = session.query(Stock).filter(Stock.symbol == symbol).first()
            if stock:
                stock.last_price_update = now
                stock.data_source = "akshare"

            existing = session.query(Recommendation).filter(
                Recommendation.symbol == symbol, Recommendation.trade_date == today
            ).first()
            if existing:
                existing.current_price = float(price)
                if pct is not None:
                    existing.price_change_pct = float(pct)
                updated += 1
            else:
                # Create new recommendation with price data
                rec = Recommendation(
                    symbol=symbol,
                    trade_date=today,
                    current_price=float(price),
                    price_change_pct=float(pct) if pct is not None else 0.0,
                )
                session.add(rec)
                updated += 1

        session.commit()

        # Cache to Redis (fire and forget — ok if Redis is down)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(cache_set_json(REALTIME_CACHE_KEY, price_data, REALTIME_CACHE_TTL))
            else:
                loop.run_until_complete(cache_set_json(REALTIME_CACHE_KEY, price_data, REALTIME_CACHE_TTL))
        except Exception:
            pass

        logger.info(f"Hourly update: {updated} prices updated")
        return len(df)
    finally:
        session.close()
