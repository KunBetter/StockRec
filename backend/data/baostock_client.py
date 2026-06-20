import logging
from typing import Optional

import baostock as bs
import pandas as pd

logger = logging.getLogger(__name__)


class BaostockClient:
    def __init__(self, timeout: int = 30, retry_count: int = 3):
        self.timeout = timeout
        self.retry_count = retry_count
        self._logged_in = False

    def login(self) -> bool:
        if self._logged_in:
            return True
        for attempt in range(self.retry_count):
            try:
                lg = bs.login()
                if lg.error_code == "0":
                    self._logged_in = True
                    logger.info("Baostock login successful")
                    return True
                logger.warning(f"Baostock login attempt {attempt+1}: {lg.error_msg}")
            except Exception as e:
                logger.error(f"Baostock login attempt {attempt+1} failed: {e}")
        return False

    def logout(self):
        if self._logged_in:
            bs.logout()
            self._logged_in = False

    def query_kline(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "2",
        fields: Optional[str] = None,
    ) -> pd.DataFrame:
        if not self.login():
            return pd.DataFrame()

        if fields is None:
            fields = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"

        try:
            rs = bs.query_history_k_data_plus(
                symbol,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjust_flag,
            )
            if rs.error_code != "0":
                logger.error(f"Baostock kline query failed: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            columns = fields.split(",")
            df = pd.DataFrame(data_list, columns=columns)

            numeric_cols = ["open", "high", "low", "close", "preclose", "volume", "amount", "turn", "pctChg"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df["symbol"] = symbol
            df["trade_date"] = pd.to_datetime(df["date"])
            return df
        except Exception as e:
            logger.error(f"Baostock kline query exception for {symbol}: {e}")
            return pd.DataFrame()

    def query_stock_list(self) -> pd.DataFrame:
        if not self.login():
            return pd.DataFrame()

        try:
            rs = bs.query_stock_basic()
            if rs.error_code != "0":
                logger.error(f"Baostock stock list query failed: {rs.error_msg}")
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            df = pd.DataFrame(data_list, columns=["code", "code_name", "ipoDate", "outDate", "type", "status"])
            # baostock already returns codes in "sh.600036" format — use directly
            df["symbol"] = df["code"]
            return df
        except Exception as e:
            logger.error(f"Baostock stock list query exception: {e}")
            return pd.DataFrame()

    def query_profit_data(self, symbol: str, year: int, quarter: int) -> pd.DataFrame:
        if not self.login():
            return pd.DataFrame()

        try:
            rs = bs.query_profit_data(code=symbol, year=year, quarter=quarter)
            if rs.error_code != "0":
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            col_names = [
                "code", "pubDate", "statDate", "roeAvg", "npMargin", "gpMargin",
                "netProfit", "epsTTM", "MBRevenue", "totalShare", "liqaShare",
            ]
            df = pd.DataFrame(data_list, columns=col_names[:len(data_list[0])])
            return df
        except Exception as e:
            logger.error(f"Baostock profit query exception for {symbol}: {e}")
            return pd.DataFrame()

    def query_balance_data(self, symbol: str, year: int, quarter: int) -> pd.DataFrame:
        if not self.login():
            return pd.DataFrame()

        try:
            rs = bs.query_balance_data(code=symbol, year=year, quarter=quarter)
            if rs.error_code != "0":
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            col_names = [
                "code", "pubDate", "statDate", "currentRatio", "quickRatio",
                "cashRatio", "YOYLiability", "liabilityToAsset", "assetToEquity",
            ]
            df = pd.DataFrame(data_list, columns=col_names[:len(data_list[0])])
            return df
        except Exception as e:
            logger.error(f"Baostock balance query exception for {symbol}: {e}")
            return pd.DataFrame()

    def query_stock_industry(self) -> pd.DataFrame:
        if not self.login():
            return pd.DataFrame()

        try:
            rs = bs.query_stock_industry()
            if rs.error_code != "0":
                return pd.DataFrame()

            data_list = []
            while rs.next():
                data_list.append(rs.get_row_data())

            if not data_list:
                return pd.DataFrame()

            # baostock returns: updateDate, code, code_name, industry, industryClassification
            df = pd.DataFrame(data_list, columns=["update_date", "code", "code_name", "industry", "industry_classification"])
            # baostock already returns codes in "sh.600036" format — use directly
            df["symbol"] = df["code"]
            return df
        except Exception as e:
            logger.error(f"Baostock industry query exception: {e}")
            return pd.DataFrame()
