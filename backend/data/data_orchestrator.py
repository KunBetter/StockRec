import logging
from typing import Optional

import pandas as pd

from backend.config import AppConfig
from backend.data.akshare_client import AKShareClient
from backend.data.baostock_client import BaostockClient
from backend.data.normalizer import normalize_kline, normalize_realtime
from backend.data.sina_client import SinaClient
from backend.data.tencent_client import TencentClient

logger = logging.getLogger(__name__)


class DataOrchestrator:
    def __init__(self, config: AppConfig):
        ds = config.data_sources
        self.config = config
        self.baostock = BaostockClient(
            timeout=ds.baostock.timeout_seconds,
            retry_count=ds.baostock.retry_count,
        )
        self.akshare = AKShareClient(
            timeout=ds.akshare.timeout_seconds,
            retry_count=ds.akshare.retry_count,
        )
        self.sina = SinaClient(
            timeout=ds.sina.timeout_seconds,
            base_url=ds.sina.base_url,
        )
        self.tencent = TencentClient(
            timeout=ds.tencent.timeout_seconds,
            base_url=ds.tencent.base_url,
        )
        self.realtime_order = ds.realtime_order
        self.history_order = ds.history_order

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """Normalize symbol to canonical sh.600036 format.

        Handles:
          - sh600036   → sh.600036 (old format without dot)
          - sz.sh.600036 → sh.600036 (corrupted double prefix)
          - sh.600036   → sh.600036 (already correct)
        """
        # Fix double-prefix: sz.sh.600036 → sh.600036
        parts = symbol.split(".")
        if len(parts) >= 3:
            # e.g. sz.sh.000001 → sh.000001
            symbol = parts[-2] + "." + parts[-1]

        # Insert dot if missing: sh600036 → sh.600036
        if "." not in symbol and len(symbol) >= 8:
            symbol = symbol[:2] + "." + symbol[2:]

        return symbol

    def fetch_realtime_prices(self, symbols: list[str]) -> pd.DataFrame:
        for source in self.realtime_order:
            df = self._fetch_realtime_from(source, symbols)
            if not df.empty:
                logger.info(f"Realtime prices from {source}: {len(df)} stocks")
                return df
        logger.warning("All realtime sources failed")
        return pd.DataFrame()

    def _fetch_realtime_from(self, source: str, symbols: list[str]) -> pd.DataFrame:
        try:
            if source == "akshare":
                df = self.akshare.get_realtime_spot()
                if not df.empty and "symbol" in df.columns:
                    df = df[df["symbol"].isin(symbols)]
                return normalize_realtime(df)
            elif source == "sina":
                return self.sina.get_realtime_quotes(symbols)
            elif source == "tencent":
                return self.tencent.get_realtime_quotes(symbols)
        except Exception as e:
            logger.warning(f"Realtime source {source} failed: {e}")
        return pd.DataFrame()

    def fetch_daily_kline(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        for source in self.history_order:
            df = self._fetch_kline_from(source, symbol, start_date, end_date)
            if not df.empty:
                return normalize_kline(df, symbol)
        logger.warning(f"All history sources failed for {symbol}")
        return pd.DataFrame()

    def _fetch_kline_from(
        self,
        source: str,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        try:
            normalized = self._normalize_symbol(symbol)
            if source == "baostock":
                return self.baostock.query_kline(normalized, start_date, end_date)
            elif source == "akshare":
                return self.akshare.get_daily_kline(normalized, start_date, end_date)
        except Exception as e:
            logger.warning(f"History source {source} failed for {symbol}: {e}")
        return pd.DataFrame()

    def sync_stock_list(self) -> pd.DataFrame:
        df = self.baostock.query_stock_list()
        if df.empty:
            logger.warning("Failed to fetch stock list")
        return df

    def sync_stock_industry(self) -> pd.DataFrame:
        return self.baostock.query_stock_industry()

    def sync_financial_data(self, symbol: str, year: int, quarter: int) -> dict:
        profit = self.baostock.query_profit_data(symbol, year, quarter)
        balance = self.baostock.query_balance_data(symbol, year, quarter)
        return {"profit": profit, "balance": balance}

    def cleanup(self):
        self.baostock.logout()
