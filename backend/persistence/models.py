import datetime
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.persistence.database import Base


def _new_uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_uuid = Column(String(32), unique=True, nullable=False, default=_new_uuid, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    nickname = Column(String(50))
    avatar_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(12), unique=True, nullable=False, index=True)
    code = Column(String(6), nullable=False)
    name = Column(String(50), nullable=False)
    exchange = Column(String(2), nullable=False)
    industry = Column(String(50))
    industry_code = Column(String(20))
    market_cap = Column(BigInteger)
    float_cap = Column(BigInteger)
    list_date = Column(Date)
    is_st = Column(Boolean, default=False)
    is_suspended = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class DailyKlineMetadata(Base):
    __tablename__ = "daily_kline_metadata"
    __table_args__ = (UniqueConstraint("symbol", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=False)
    symbol = Column(String(12), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    preclose = Column(Float)
    volume = Column(BigInteger)
    amount = Column(Float)
    adjust_flag = Column(Integer, default=2)
    turn_rate = Column(Float)
    pct_change = Column(Float)
    is_st = Column(Boolean, default=False)
    parquet_file = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FinancialData(Base):
    __tablename__ = "financial_data"
    __table_args__ = (UniqueConstraint("symbol", "report_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, nullable=False)
    symbol = Column(String(12), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    report_type = Column(String(10))

    revenue = Column(Float)
    operating_cost = Column(Float)
    operating_profit = Column(Float)
    net_profit = Column(Float)
    net_profit_parent = Column(Float)
    eps = Column(Float)
    rd_expense = Column(Float)

    total_assets = Column(Float)
    total_liabilities = Column(Float)
    net_assets = Column(Float)
    current_assets = Column(Float)
    current_liabilities = Column(Float)

    operating_cf = Column(Float)
    investing_cf = Column(Float)
    financing_cf = Column(Float)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FactorScore(Base):
    __tablename__ = "factor_scores"
    __table_args__ = (UniqueConstraint("symbol", "calc_date", "factor_name"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(12), nullable=False, index=True)
    calc_date = Column(Date, nullable=False, index=True)
    factor_name = Column(String(50), nullable=False)
    raw_value = Column(Float)
    z_score = Column(Float)
    percentile = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("symbol", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(12), nullable=False)
    trade_date = Column(Date, nullable=False, index=True)

    layer1_factor_score = Column(Float)
    layer2_ml_score = Column(Float)
    layer3_event_score = Column(Float)

    predicted_return = Column(Float)
    momentum_score = Column(Float)
    quality_score = Column(Float)
    sentiment_score = Column(Float)

    composite_score = Column(Float, index=True)
    rank = Column(Integer)
    risk_level = Column(String(10), index=True)
    risk_score = Column(Float)

    current_price = Column(Float)
    price_change_pct = Column(Float)
    market_cap = Column(BigInteger)
    holding_period = Column(String(20))

    ai_summary = Column(Text)
    ai_full_analysis = Column(Text)
    ai_risk_flags = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class NewsSentiment(Base):
    __tablename__ = "news_sentiment"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(12), nullable=False, index=True)
    news_date = Column(Date, nullable=False, index=True)
    news_time = Column(DateTime)
    title = Column(Text, nullable=False)
    source = Column(String(100))
    url = Column(Text)
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    relevance_score = Column(Float)
    ai_processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FundFlow(Base):
    __tablename__ = "fund_flows"
    __table_args__ = (UniqueConstraint("symbol", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(12), nullable=False, index=True)
    trade_date = Column(Date, nullable=False, index=True)
    main_net_inflow = Column(Float)
    super_large_inflow = Column(Float)
    large_inflow = Column(Float)
    medium_inflow = Column(Float)
    small_inflow = Column(Float)
    northbound_holding = Column(Float)
    northbound_pct = Column(Float)
    margin_balance = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_name = Column(String(100), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, index=True)
    finished_at = Column(DateTime)
    status = Column(String(20), default="running")
    error_message = Column(Text)
    records_processed = Column(Integer)
    duration_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MarketIndex(Base):
    __tablename__ = "market_indices"
    __table_args__ = (UniqueConstraint("index_code", "trade_date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    index_code = Column(String(20), nullable=False)
    index_name = Column(String(50), nullable=False)
    trade_date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)
    amount = Column(Float)
    pct_change = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "symbol"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol = Column(String(12), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
