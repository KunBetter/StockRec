import json
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from backend.api.schemas import AnalysisResponse
from backend.persistence.database import get_session
from backend.persistence.models import Recommendation, Stock, NewsSentiment

router = APIRouter()


@router.get("/analysis/{symbol}")
def get_analysis(symbol: str, target_date: Optional[str] = None, request: Request = None):
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
            raise HTTPException(status_code=404, detail="No analysis available")

        s = session.query(Stock).filter(Stock.symbol == symbol).first()
        stock_name = s.name if s else symbol

        # Parse AI analysis
        ai_full = {}
        if rec.ai_full_analysis:
            try:
                ai_full = json.loads(rec.ai_full_analysis)
            except json.JSONDecodeError:
                pass

        risk_flags = []
        if rec.ai_risk_flags:
            try:
                risk_flags = json.loads(rec.ai_risk_flags)
            except json.JSONDecodeError:
                pass

        # Build score breakdown
        cw = {"predicted_return": 0.5, "momentum_score": 0.2, "quality_score": 0.2, "sentiment_score": 0.1}
        score_breakdown = {}
        if rec.predicted_return is not None:
            score_breakdown["predicted_return"] = {
                "value": rec.predicted_return,
                "weight": cw["predicted_return"],
                "contribution": rec.predicted_return * cw["predicted_return"],
            }
        if rec.momentum_score is not None:
            score_breakdown["momentum_score"] = {
                "value": rec.momentum_score,
                "weight": cw["momentum_score"],
                "contribution": rec.momentum_score * cw["momentum_score"],
            }
        if rec.quality_score is not None:
            score_breakdown["quality_score"] = {
                "value": rec.quality_score,
                "weight": cw["quality_score"],
                "contribution": rec.quality_score * cw["quality_score"],
            }
        if rec.sentiment_score is not None:
            score_breakdown["sentiment_score"] = {
                "value": rec.sentiment_score,
                "weight": cw["sentiment_score"],
                "contribution": rec.sentiment_score * cw["sentiment_score"],
            }

        return AnalysisResponse(
            symbol=symbol,
            name=stock_name,
            date=rec.trade_date if rec.trade_date else date.today(),
            composite_score=rec.composite_score,
            score_breakdown=score_breakdown,
            layer_scores={
                "layer1_factor": rec.layer1_factor_score,
                "layer2_ml": rec.layer2_ml_score,
                "layer3_event": rec.layer3_event_score,
            },
            ai_analysis={
                "recommendation": rec.ai_summary,
                "financial": ai_full.get("financial", {}),
                "news": ai_full.get("news", {}),
                "industry": ai_full.get("industry", {}),
                "risk_flags": risk_flags,
            },
            key_metrics={
                "predicted_return": rec.predicted_return,
                "momentum_score": rec.momentum_score,
                "quality_score": rec.quality_score,
                "sentiment_score": rec.sentiment_score,
                "risk_level": rec.risk_level,
            },
        ).model_dump()
    finally:
        session.close()


@router.get("/analysis/{symbol}/news")
def get_stock_news(symbol: str, limit: int = Query(20, le=50)):
    session = get_session()
    try:
        items = (
            session.query(NewsSentiment)
            .filter(NewsSentiment.symbol == symbol)
            .order_by(NewsSentiment.news_date.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "date": str(n.news_date) if n.news_date else None,
                "title": n.title,
                "source": n.source,
                "sentiment_label": n.sentiment_label,
                "sentiment_score": n.sentiment_score,
            }
            for n in items
        ]
    finally:
        session.close()
