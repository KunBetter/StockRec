from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class StockBrief(BaseModel):
    symbol: str
    code: str
    name: str
    exchange: str
    industry: Optional[str] = None
    market_cap: Optional[int] = None
    status: str = "active"

    class Config:
        from_attributes = True


class StockDetail(BaseModel):
    symbol: str
    code: str
    name: str
    exchange: str
    industry: Optional[str] = None
    industry_code: Optional[str] = None
    market_cap: Optional[int] = None
    float_cap: Optional[int] = None
    list_date: Optional[date] = None
    is_st: bool = False
    is_suspended: bool = False
    status: str = "active"

    class Config:
        from_attributes = True


class KlineDataPoint(BaseModel):
    trade_date: date
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    amount: Optional[float] = None
    pct_change: Optional[float] = None
    turn_rate: Optional[float] = None


class FinancialDataPoint(BaseModel):
    report_date: date
    revenue: Optional[float] = None
    net_profit: Optional[float] = None
    eps: Optional[float] = None
    total_assets: Optional[float] = None
    net_assets: Optional[float] = None
    roe: Optional[float] = None


class FactorScorePoint(BaseModel):
    calc_date: date
    factor_name: str
    raw_value: Optional[float] = None
    z_score: Optional[float] = None
    percentile: Optional[float] = None


class StockRecommendationItem(BaseModel):
    symbol: str
    name: str = ""
    current_price: Optional[float] = None
    price_change_pct: Optional[float] = None
    predicted_return: Optional[float] = None
    momentum_score: Optional[float] = None
    quality_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    composite_score: Optional[float] = None
    rank: Optional[int] = None
    risk_level: Optional[str] = None
    market_cap: Optional[int] = None
    holding_period: Optional[str] = None
    ai_summary: Optional[str] = None
    industry: Optional[str] = None
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None


class RiskSection(BaseModel):
    risk_level: str
    label: str
    description: str
    stocks: list[StockRecommendationItem]


class MarketSummary(BaseModel):
    index_name: str = "上证指数"
    index_value: Optional[float] = None
    change_pct: Optional[float] = None
    market_status: str = "open"


class RecommendationsResponse(BaseModel):
    date: date
    generated_at: Optional[datetime] = None
    market_summary: Optional[MarketSummary] = None
    sections: list[RiskSection]


class ScoreBreakdownItem(BaseModel):
    value: float
    weight: float
    contribution: float


class AnalysisResponse(BaseModel):
    symbol: str
    name: str
    date: date
    composite_score: Optional[float] = None
    score_breakdown: Optional[dict] = None
    layer_scores: Optional[dict] = None
    ai_analysis: Optional[dict] = None
    key_metrics: Optional[dict] = None
    peer_rank: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    components: dict


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
