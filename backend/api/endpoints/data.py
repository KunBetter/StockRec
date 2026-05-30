from datetime import date, datetime

from fastapi import APIRouter, Request

from backend.persistence.database import get_session
from backend.persistence.models import Stock

router = APIRouter()


@router.get("/data/freshness")
def get_data_freshness(request: Request):
    session = get_session()
    try:
        stocks = session.query(Stock).filter(Stock.status == "active").all()

        sources = {}
        for s in stocks:
            if s.data_source:
                sources[s.data_source] = sources.get(s.data_source, 0) + 1

        latest_update = None
        for s in stocks:
            if s.last_price_update:
                if latest_update is None or s.last_price_update > latest_update:
                    latest_update = s.last_price_update

        return {
            "status": "ok",
            "latest_update": latest_update.isoformat() if latest_update else None,
            "stock_count": len(stocks),
            "sources": sources,
            "is_realtime": latest_update is not None and (datetime.utcnow() - latest_update).total_seconds() < 3600,
        }
    finally:
        session.close()
