from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, get_optional_user
from backend.persistence.database import get_async_engine, get_session, is_postgres
from backend.persistence.models import ExecutionLog, Recommendation, Stock, User, WatchlistItem

router = APIRouter()


async def _get_db() -> AsyncSession:
    """Get async session if PostgreSQL, otherwise fall back to sync."""
    engine = get_async_engine()
    if engine is not None:
        from sqlalchemy.ext.asyncio import async_sessionmaker

        sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        async with sessionmaker() as session:
            yield session
    else:
        yield None


def _get_user_id(user_uuid: str) -> int | None:
    """Resolve user_uuid to internal user_id."""
    db: Session = get_session()
    try:
        user = db.execute(select(User).where(User.user_uuid == user_uuid)).scalar_one_or_none()
        return user.id if user else None
    finally:
        db.close()


def _get_db_sync():
    """Get sync session for SQLite fallback."""
    db: Session = get_session()
    try:
        yield db
    finally:
        db.close()


@router.get("/profile/watchlist")
def get_watchlist(user_uuid: str = Depends(get_current_user)):
    db: Session = get_session()
    try:
        user = db.execute(select(User).where(User.user_uuid == user_uuid)).scalar_one_or_none()
        if not user:
            return {"count": 0, "items": []}

        watch_items = (
            db.execute(select(WatchlistItem).where(WatchlistItem.user_id == user.id))
            .scalars()
            .all()
        )
        symbols = [w.symbol for w in watch_items]

        stocks = db.execute(select(Stock).where(Stock.symbol.in_(symbols))).scalars().all() if symbols else []
        stock_map = {s.symbol: s for s in stocks}

        items = []
        for sym in symbols:
            s = stock_map.get(sym)
            if not s:
                continue
            rec = (
                db.execute(
                    select(Recommendation)
                    .where(Recommendation.symbol == sym)
                    .order_by(Recommendation.trade_date.desc())
                )
                .scalars()
                .first()
            )
            items.append({
                "symbol": s.symbol,
                "name": s.name,
                "industry": s.industry,
                "market_cap": s.market_cap,
                "current_price": rec.current_price if rec else None,
                "price_change_pct": rec.price_change_pct if rec else None,
                "composite_score": rec.composite_score if rec else None,
                "risk_level": rec.risk_level if rec else None,
            })

        return {"count": len(items), "items": items}
    finally:
        db.close()


@router.post("/profile/watchlist/{symbol}")
def add_to_watchlist(symbol: str, user_uuid: str = Depends(get_current_user)):
    db: Session = get_session()
    try:
        user = db.execute(select(User).where(User.user_uuid == user_uuid)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        stock = db.execute(select(Stock).where(Stock.symbol == symbol)).scalar_one_or_none()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")

        existing = db.execute(
            select(WatchlistItem).where(
                WatchlistItem.user_id == user.id,
                WatchlistItem.symbol == symbol,
            )
        ).scalar_one_or_none()

        if existing:
            return {"success": True, "symbol": symbol, "message": "Already in watchlist"}

        item = WatchlistItem(user_id=user.id, symbol=symbol)
        db.add(item)
        db.commit()

        count = db.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user.id)
        ).scalars().all()

        return {"success": True, "symbol": symbol, "watchlist_size": len(count)}
    finally:
        db.close()


@router.delete("/profile/watchlist/{symbol}")
def remove_from_watchlist(symbol: str, user_uuid: str = Depends(get_current_user)):
    db: Session = get_session()
    try:
        user = db.execute(select(User).where(User.user_uuid == user_uuid)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        db.execute(
            delete(WatchlistItem).where(
                WatchlistItem.user_id == user.id,
                WatchlistItem.symbol == symbol,
            )
        )
        db.commit()

        count = db.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user.id)
        ).scalars().all()

        return {"success": True, "symbol": symbol, "watchlist_size": len(count)}
    finally:
        db.close()


@router.get("/profile/history")
def get_recommendation_history(
    limit: int = Query(20, le=50),
    risk: Optional[str] = None,
):
    db: Session = get_session()
    try:
        query = (
            select(Recommendation)
            .order_by(Recommendation.trade_date.desc(), Recommendation.composite_score.desc())
        )
        if risk:
            query = query.where(Recommendation.risk_level == risk)
        items = db.execute(query.limit(limit)).scalars().all()

        stocks = db.execute(select(Stock)).scalars().all()
        stock_names = {s.symbol: s.name for s in stocks}

        return [
            {
                "symbol": r.symbol,
                "name": stock_names.get(r.symbol, r.symbol),
                "trade_date": str(r.trade_date) if r.trade_date else None,
                "composite_score": r.composite_score,
                "predicted_return": r.predicted_return,
                "risk_level": r.risk_level,
                "rank": r.rank,
                "ai_summary": r.ai_summary,
            }
            for r in items
        ]
    finally:
        db.close()


@router.get("/profile/status")
def get_system_status(user_uuid: str = Depends(get_current_user)):
    db: Session = get_session()
    try:
        user = db.execute(select(User).where(User.user_uuid == user_uuid)).scalar_one_or_none()
        user_id = user.id if user else None

        latest_rec = db.execute(
            select(Recommendation.trade_date).order_by(Recommendation.trade_date.desc())
        ).first()
        last_update = str(latest_rec[0]) if latest_rec else None

        stock_count = db.execute(
            select(Stock).where(Stock.status == "active")
        ).scalars().all()

        watchlist_count = 0
        if user_id:
            watch_items = db.execute(
                select(WatchlistItem).where(WatchlistItem.user_id == user_id)
            ).scalars().all()
            watchlist_count = len(watch_items)

        recent_jobs = db.execute(
            select(ExecutionLog).order_by(ExecutionLog.started_at.desc()).limit(5)
        ).scalars().all()

        job_status = [
            {
                "job_name": j.job_name.replace("_", " ").title(),
                "status": j.status,
                "started_at": str(j.started_at) if j.started_at else None,
                "duration_ms": j.duration_ms,
            }
            for j in recent_jobs
        ]

        return {
            "last_update": last_update,
            "stock_count": len(stock_count),
            "watchlist_count": watchlist_count,
            "database_ok": True,
            "recent_jobs": job_status,
        }
    finally:
        db.close()
