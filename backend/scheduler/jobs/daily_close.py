import logging
from datetime import date, datetime, timedelta

import pandas as pd

from backend.config import AppConfig
from backend.data.data_orchestrator import DataOrchestrator
from backend.persistence.database import get_session
from backend.persistence.models import Stock, DailyKlineMetadata
from backend.persistence.parquet_store import ParquetStore
from backend.persistence.repository import Repository

logger = logging.getLogger(__name__)


def run_daily_close(config: AppConfig) -> int:
    session = get_session()
    try:
        stock_repo = Repository(session, Stock)
        stocks = stock_repo.find_by(status="active")
        if not stocks:
            logger.warning("No active stocks for daily close")
            return 0

        orch = DataOrchestrator(config)
        parquet = ParquetStore(
            base_path=config.persistence.parquet.base_path,
            compression=config.persistence.parquet.compression,
        )

        today = date.today()
        start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")

        total_records = 0
        for stock in stocks:
            try:
                df = orch.fetch_daily_kline(stock.symbol, start_date, end_date)
                if df.empty:
                    continue

                parquet.write_kline(stock.symbol, df)

                # Update metadata index
                meta_repo = Repository(session, DailyKlineMetadata)
                for _, row in df.iterrows():
                    trade_date = row.get("trade_date")
                    if isinstance(trade_date, pd.Timestamp):
                        trade_date = trade_date.date()
                    elif isinstance(trade_date, datetime):
                        trade_date = trade_date.date()

                    meta_repo.upsert(
                        unique_keys={"symbol": stock.symbol, "trade_date": trade_date},
                        data={
                            "stock_id": stock.id,
                            "symbol": stock.symbol,
                            "trade_date": trade_date,
                            "open": float(row["open"]) if pd.notna(row.get("open")) else None,
                            "high": float(row["high"]) if pd.notna(row.get("high")) else None,
                            "low": float(row["low"]) if pd.notna(row.get("low")) else None,
                            "close": float(row["close"]) if pd.notna(row.get("close")) else None,
                            "preclose": float(row["preclose"]) if pd.notna(row.get("preclose")) else None,
                            "volume": int(row["volume"]) if pd.notna(row.get("volume")) else 0,
                            "amount": float(row["amount"]) if pd.notna(row.get("amount")) else 0,
                            "pct_change": float(row["pct_change"]) if pd.notna(row.get("pct_change")) else None,
                            "turn_rate": float(row["turn_rate"]) if pd.notna(row.get("turn_rate")) else None,
                            "parquet_file": str(parquet._kline_file(stock.symbol, trade_date.year)),
                        },
                    )
                total_records += len(df)
            except Exception as e:
                logger.error(f"Daily close failed for {stock.symbol}: {e}")

        session.commit()
        orch.cleanup()
        logger.info(f"Daily close: {total_records} kline records synced for {len(stocks)} stocks")
        return total_records
    finally:
        session.close()
