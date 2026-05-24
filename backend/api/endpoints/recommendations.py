from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from backend.api.schemas import (
    RecommendationsResponse,
    StockRecommendationItem,
    RiskSection,
    MarketSummary,
)
from backend.persistence.database import get_session
from backend.persistence.models import Recommendation, Stock

router = APIRouter()

RISK_LABELS = {
    "low": "低风险",
    "medium": "中风险",
    "high": "高风险",
}

RISK_DESCRIPTIONS = {
    "low": "低波动，稳定增长，适合稳健型投资者",
    "medium": "中等波动，成长性较好，适合平衡型投资者",
    "high": "高波动，高弹性，适合进取型投资者",
}


def get_config(request: Request):
    return request.app.state.config


@router.get("/recommendations")
def get_recommendations(
    request: Request,
    target_date: Optional[str] = None,
    limit: int = Query(30, ge=10, le=50),
    price_min: Optional[float] = Query(None, description="最低价格"),
    price_max: Optional[float] = Query(None, description="最高价格"),
):
    session = get_session()
    try:
        if target_date:
            trade_date = target_date
        else:
            # Get latest available date
            latest = (
                session.query(Recommendation.trade_date)
                .order_by(Recommendation.trade_date.desc())
                .first()
            )
            trade_date = str(latest[0]) if latest else str(date.today())

        query = (
            session.query(Recommendation)
            .filter(Recommendation.trade_date == trade_date)
        )
        if price_min is not None:
            query = query.filter(Recommendation.current_price >= price_min)
        if price_max is not None:
            query = query.filter(Recommendation.current_price <= price_max)

        recs = (
            query.order_by(Recommendation.composite_score.desc())
            .limit(limit)
            .all()
        )

        if not recs:
            return RecommendationsResponse(
                date=date.today(),
                generated_at=datetime.utcnow(),
                market_summary=MarketSummary(market_status="no_data"),
                sections=[],
            ).model_dump()

        # Enrich with stock names
        stock_repo = {}
        for rec in recs:
            if rec.symbol not in stock_repo:
                s = session.query(Stock).filter(Stock.symbol == rec.symbol).first()
                stock_repo[rec.symbol] = s.name if s else rec.symbol

        # Group by risk level
        sections_data = {"low": [], "medium": [], "high": []}
        for rec in recs:
            risk = rec.risk_level or "medium"
            if risk not in sections_data:
                risk = "medium"

            item = StockRecommendationItem(
                symbol=rec.symbol,
                name=stock_repo.get(rec.symbol, rec.symbol),
                current_price=rec.current_price,
                price_change_pct=rec.price_change_pct,
                predicted_return=rec.predicted_return,
                momentum_score=rec.momentum_score,
                quality_score=rec.quality_score,
                sentiment_score=rec.sentiment_score,
                composite_score=rec.composite_score,
                rank=rec.rank,
                risk_level=rec.risk_level,
                market_cap=rec.market_cap,
                holding_period=rec.holding_period,
                ai_summary=rec.ai_summary,
            )
            sections_data[risk].append(item)

        sections = []
        for risk_level in ["low", "medium", "high"]:
            items = sections_data[risk_level]
            if items:
                items.sort(key=lambda x: x.composite_score or 0, reverse=True)
                sections.append(
                    RiskSection(
                        risk_level=risk_level,
                        label=RISK_LABELS[risk_level],
                        description=RISK_DESCRIPTIONS[risk_level],
                        stocks=items,
                    )
                )

        return RecommendationsResponse(
            date=date.today(),
            generated_at=datetime.utcnow(),
            market_summary=MarketSummary(),
            sections=sections,
        ).model_dump()
    finally:
        session.close()


@router.get("/recommendations/{symbol}")
def get_recommendation_detail(symbol: str, target_date: Optional[str] = None, request: Request = None):
    session = get_session()
    try:
        if target_date:
            rec = (
                session.query(Recommendation)
                .filter(Recommendation.symbol == symbol, Recommendation.trade_date == target_date)
                .first()
            )
        else:
            rec = (
                session.query(Recommendation)
                .filter(Recommendation.symbol == symbol)
                .order_by(Recommendation.trade_date.desc())
                .first()
            )

        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        s = session.query(Stock).filter(Stock.symbol == symbol).first()
        return {
            "symbol": rec.symbol,
            "name": s.name if s else rec.symbol,
            "date": str(rec.trade_date) if rec.trade_date else None,
            "composite_score": rec.composite_score,
            "layer1_factor_score": rec.layer1_factor_score,
            "layer2_ml_score": rec.layer2_ml_score,
            "layer3_event_score": rec.layer3_event_score,
            "predicted_return": rec.predicted_return,
            "momentum_score": rec.momentum_score,
            "quality_score": rec.quality_score,
            "sentiment_score": rec.sentiment_score,
            "risk_level": rec.risk_level,
            "risk_score": rec.risk_score,
            "current_price": rec.current_price,
            "price_change_pct": rec.price_change_pct,
            "ai_summary": rec.ai_summary,
            "ai_full_analysis": rec.ai_full_analysis,
            "ai_risk_flags": rec.ai_risk_flags,
        }
    finally:
        session.close()
