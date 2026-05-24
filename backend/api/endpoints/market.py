from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Query, Request

from backend.api.schemas import MarketSummary
from backend.persistence.database import get_session
from backend.persistence.models import MarketIndex, Stock, Recommendation

router = APIRouter()


@router.get("/market/summary")
def get_market_summary(request: Request):
    session = get_session()
    try:
        latest_index = (
            session.query(MarketIndex)
            .filter(MarketIndex.index_code == "sh000001")
            .order_by(MarketIndex.trade_date.desc())
            .first()
        )

        if latest_index:
            return MarketSummary(
                index_name="上证指数",
                index_value=latest_index.close,
                change_pct=latest_index.pct_change,
                market_status="open",
            ).model_dump()

        return MarketSummary(market_status="no_data").model_dump()
    finally:
        session.close()


@router.get("/market/indices")
def get_market_indices(
    request: Request,
    index_code: str = Query("sh000001"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    session = get_session()
    try:
        query = session.query(MarketIndex).filter(MarketIndex.index_code == index_code)
        if start_date:
            query = query.filter(MarketIndex.trade_date >= start_date)
        if end_date:
            query = query.filter(MarketIndex.trade_date <= end_date)
        items = query.order_by(MarketIndex.trade_date).all()

        return [
            {
                "trade_date": str(i.trade_date) if i.trade_date else None,
                "open": i.open,
                "high": i.high,
                "low": i.low,
                "close": i.close,
                "volume": i.volume,
                "amount": i.amount,
                "pct_change": i.pct_change,
            }
            for i in items
        ]
    finally:
        session.close()


@router.get("/market/overview")
def get_market_overview():
    """Full market overview: indices, breadth, sectors, top movers."""
    session = get_session()
    try:
        today = date.today()

        # Demo indices data
        indices = [
            {"name": "上证指数", "code": "000001", "value": 3350.12, "change_pct": 0.35, "change_amount": 11.73},
            {"name": "深证成指", "code": "399001", "value": 10820.45, "change_pct": 0.62, "change_amount": 66.80},
            {"name": "创业板指", "code": "399006", "value": 2215.33, "change_pct": 1.25, "change_amount": 27.38},
            {"name": "科创50", "code": "000688", "value": 985.60, "change_pct": 0.88, "change_amount": 8.60},
        ]

        # Market breadth (demo data)
        try:
            stock_count = session.query(Stock).filter(Stock.status == "active").count()
        except Exception:
            stock_count = 20

        breadth = {
            "up": 12, "down": 7, "flat": 1,
            "up_pct": 60.0, "down_pct": 35.0, "flat_pct": 5.0,
            "volume_billion": 856.32,
            "limit_up": 45, "limit_down": 12,
        }

        # Sector performance (demo)
        sectors = [
            {"name": "新能源", "change_pct": 3.25, "leader": "宁德时代", "leader_change": 5.2},
            {"name": "半导体", "change_pct": 2.85, "leader": "中芯国际", "leader_change": 4.1},
            {"name": "白酒", "change_pct": 2.10, "leader": "贵州茅台", "leader_change": 2.8},
            {"name": "银行", "change_pct": -0.45, "leader": "招商银行", "leader_change": -0.3},
            {"name": "医药", "change_pct": -0.82, "leader": "恒瑞医药", "leader_change": -1.1},
            {"name": "电力", "change_pct": 0.55, "leader": "长江电力", "leader_change": 0.8},
            {"name": "家电", "change_pct": -0.15, "leader": "美的集团", "leader_change": -0.2},
            {"name": "汽车", "change_pct": 4.10, "leader": "比亚迪", "leader_change": 6.5},
        ]
        sectors.sort(key=lambda x: x["change_pct"], reverse=True)

        # Top movers from recommendations
        try:
            top_recs = (
                session.query(Recommendation)
                .filter(Recommendation.trade_date == today)
                .filter(Recommendation.price_change_pct.isnot(None))
                .order_by(Recommendation.price_change_pct.desc())
                .limit(5)
                .all()
            )
            top_gainers = [
                {"symbol": r.symbol, "name": r.symbol, "change_pct": r.price_change_pct}
                for r in top_recs
            ]
        except Exception:
            top_gainers = []

        try:
            bottom_recs = (
                session.query(Recommendation)
                .filter(Recommendation.trade_date == today)
                .filter(Recommendation.price_change_pct.isnot(None))
                .order_by(Recommendation.price_change_pct.asc())
                .limit(5)
                .all()
            )
            top_losers = [
                {"symbol": r.symbol, "name": r.symbol, "change_pct": r.price_change_pct}
                for r in bottom_recs
            ]
        except Exception:
            top_losers = []

        # Enrich with stock names
        stock_names = {}
        stocks = session.query(Stock).all()
        for s in stocks:
            stock_names[s.symbol] = s.name

        for g in top_gainers:
            g["name"] = stock_names.get(g["symbol"], g["symbol"])
        for l in top_losers:
            l["name"] = stock_names.get(l["symbol"], l["symbol"])

        return {
            "date": str(today),
            "indices": indices,
            "breadth": breadth,
            "sectors": sectors,
            "top_gainers": top_gainers,
            "top_losers": top_losers,
        }
    finally:
        session.close()
