import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class AKShareClient:
    def __init__(self, timeout: int = 30, retry_count: int = 2):
        self.timeout = timeout
        self.retry_count = retry_count

    def get_realtime_spot(self) -> pd.DataFrame:
        try:
            import akshare as ak
            df = ak.stock_zh_a_spot_em()
            if df is not None and not df.empty:
                df = df.rename(columns={
                    "代码": "code",
                    "名称": "name",
                    "最新价": "price",
                    "涨跌幅": "pct_change",
                    "涨跌额": "change_amount",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "最高": "high",
                    "最低": "low",
                    "今开": "open",
                    "昨收": "preclose",
                    "换手率": "turn_rate",
                    "市盈率-动态": "pe_dynamic",
                    "市净率": "pb",
                    "总市值": "market_cap",
                    "流通市值": "float_cap",
                })
                df["symbol"] = df["code"].apply(self._code_to_symbol)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"AKShare realtime spot failed: {e}")
            return pd.DataFrame()

    def get_daily_kline(
        self, symbol: str, start_date: str, end_date: str, adjust: str = "qfq"
    ) -> pd.DataFrame:
        try:
            import akshare as ak
            code = symbol.replace("sh.", "").replace("sz.", "")
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust=adjust,
            )
            if df is not None and not df.empty:
                df = df.rename(columns={
                    "日期": "trade_date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "pct_change",
                    "涨跌额": "change_amount",
                    "换手率": "turn_rate",
                })
                df["symbol"] = symbol
                df["trade_date"] = pd.to_datetime(df["trade_date"])
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"AKShare kline failed for {symbol}: {e}")
            return pd.DataFrame()

    def get_fund_flow(self, code: str) -> pd.DataFrame:
        try:
            import akshare as ak
            market = "sz" if code.startswith(("0", "3")) else "sh"
            df = ak.stock_individual_fund_flow(stock=code, market=market)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"AKShare fund flow failed for {code}: {e}")
            return pd.DataFrame()

    def get_news(self, code: str) -> pd.DataFrame:
        try:
            import akshare as ak
            df = ak.stock_news_em(symbol=code)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.error(f"AKShare news failed for {code}: {e}")
            return pd.DataFrame()

    @staticmethod
    def _code_to_symbol(code: str) -> str:
        if code.startswith(("6", "9")):
            return f"sh.{code}"
        return f"sz.{code}"
