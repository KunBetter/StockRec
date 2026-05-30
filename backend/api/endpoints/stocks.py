from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.api.schemas import (
    StockBrief,
    StockDetail,
    KlineDataPoint,
    FinancialDataPoint,
    FactorScorePoint,
    PaginatedResponse,
)
from backend.persistence.database import get_session
from backend.persistence.models import Recommendation, Stock, DailyKlineMetadata, FinancialData, FactorScore
from backend.persistence.parquet_store import ParquetStore
from backend.persistence.repository import Repository

router = APIRouter()


def get_config(request: Request):
    return request.app.state.config


@router.get("/stocks", response_model=PaginatedResponse)
def list_stocks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    industry: Optional[str] = None,
    status: str = "active",
):
    session = get_session()
    try:
        repo = Repository(session, Stock)
        query = session.query(Stock)

        if status:
            query = query.filter(Stock.status == status)
        if industry:
            query = query.filter(Stock.industry == industry)
        if search:
            query = query.filter(
                (Stock.name.contains(search)) | (Stock.symbol.contains(search))
            )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": [StockBrief.model_validate(s).model_dump() for s in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    finally:
        session.close()


@router.get("/stocks/{symbol}")
def get_stock_detail(symbol: str, request: Request):
    session = get_session()
    try:
        repo = Repository(session, Stock)
        stock = repo.find_one_by(symbol=symbol)
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")
        return StockDetail.model_validate(stock).model_dump()
    finally:
        session.close()


@router.get("/stocks/{symbol}/kline")
def get_stock_kline(
    symbol: str,
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    config = get_config(request)
    parquet = ParquetStore(
        base_path=config.persistence.parquet.base_path,
        compression=config.persistence.parquet.compression,
    )
    df = parquet.read_kline(symbol, start_date, end_date)
    if df.empty:
        return []

    records = []
    for _, row in df.iterrows():
        records.append({
            "trade_date": str(row.get("trade_date", ""))[:10] if pd.notna(row.get("trade_date")) else None,
            "open": float(row["open"]) if pd.notna(row.get("open")) else None,
            "high": float(row["high"]) if pd.notna(row.get("high")) else None,
            "low": float(row["low"]) if pd.notna(row.get("low")) else None,
            "close": float(row["close"]) if pd.notna(row.get("close")) else None,
            "volume": int(row["volume"]) if pd.notna(row.get("volume")) else None,
            "amount": float(row["amount"]) if pd.notna(row.get("amount")) else None,
            "pct_change": float(row["pct_change"]) if pd.notna(row.get("pct_change")) else None,
            "turn_rate": float(row["turn_rate"]) if pd.notna(row.get("turn_rate")) else None,
        })
    return records


@router.get("/stocks/{symbol}/financials")
def get_stock_financials(symbol: str, request: Request):
    session = get_session()
    try:
        repo = Repository(session, FinancialData)
        items = repo.find_by(symbol=symbol)
        return [
            {
                "report_date": str(f.report_date) if f.report_date else None,
                "revenue": f.revenue,
                "net_profit": f.net_profit_parent or f.net_profit,
                "eps": f.eps,
                "total_assets": f.total_assets,
                "net_assets": f.net_assets,
            }
            for f in items
        ]
    finally:
        session.close()


@router.get("/stocks/{symbol}/factors")
def get_stock_factors(
    symbol: str,
    request: Request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    session = get_session()
    try:
        query = session.query(FactorScore).filter(FactorScore.symbol == symbol)
        if start_date:
            query = query.filter(FactorScore.calc_date >= start_date)
        if end_date:
            query = query.filter(FactorScore.calc_date <= end_date)
        items = query.order_by(FactorScore.calc_date).all()

        return [
            {
                "calc_date": str(f.calc_date) if f.calc_date else None,
                "factor_name": f.factor_name,
                "raw_value": f.raw_value,
                "z_score": f.z_score,
                "percentile": f.percentile,
            }
            for f in items
        ]
    finally:
        session.close()


class CompareRequest(BaseModel):
    symbols: list[str]


@router.post("/stocks/compare")
def compare_stocks(body: CompareRequest, request: Request):
    session = get_session()
    try:
        latest = session.query(Recommendation.trade_date).order_by(Recommendation.trade_date.desc()).first()
        trade_date = str(latest[0]) if latest else str(date.today())

        columns = []
        for symbol in body.symbols:
            rec = session.query(Recommendation).filter(
                Recommendation.symbol == symbol, Recommendation.trade_date == trade_date
            ).first()
            stock = session.query(Stock).filter(Stock.symbol == symbol).first()
            if not rec:
                continue

            metrics = {
                "composite_score": rec.composite_score,
                "predicted_return": rec.predicted_return,
                "momentum_score": rec.momentum_score,
                "quality_score": rec.quality_score,
                "sentiment_score": rec.sentiment_score,
                "current_price": rec.current_price,
                "price_change_pct": rec.price_change_pct,
                "pe": None, "roe": None, "dividend_yield": None,
                "market_cap": rec.market_cap,
                "risk_level": rec.risk_level,
            }
            columns.append({
                "symbol": symbol,
                "name": stock.name if stock else symbol,
                "metrics": metrics,
            })

        verdict = None
        if len(columns) >= 2:
            names_scores = [(c["name"], c["metrics"]["composite_score"]) for c in columns]
            best = max(names_scores, key=lambda x: x[1] or 0)
            verdict = f"综合评分最高的是{best[0]}（{best[1]:.0f}分）。"

        return {"columns": columns, "ai_verdict": verdict}
    finally:
        session.close()


# Import at bottom to avoid circular import
import pandas as pd
