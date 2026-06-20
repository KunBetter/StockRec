import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


class ParquetStore:
    def __init__(self, base_path: str = "data/parquet", compression: str = "snappy"):
        self.base_path = Path(base_path)
        if not self.base_path.is_absolute():
            self.base_path = Path(__file__).resolve().parent.parent.parent / base_path
        self.compression = compression

    @staticmethod
    def _norm_symbol(symbol: str) -> str:
        """Normalize symbol to canonical sh.600036 format for directory naming."""
        if "." not in symbol and len(symbol) >= 8:
            symbol = symbol[:2] + "." + symbol[2:]
        return symbol

    def _kline_dir(self, symbol: str) -> Path:
        return self.base_path / "kline" / self._norm_symbol(symbol)

    def _kline_file(self, symbol: str, year: int) -> Path:
        return self._kline_dir(symbol) / f"{year}.parquet"

    def write_kline(self, symbol: str, df: pd.DataFrame) -> str:
        df = df.copy()
        if "trade_date" not in df.columns and "date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["date"]).dt.date
        if "trade_date" in df.columns:
            df["trade_date"] = pd.to_datetime(df["trade_date"])
            df["year"] = pd.to_datetime(df["trade_date"]).dt.year

        out_dir = self._kline_dir(symbol)
        out_dir.mkdir(parents=True, exist_ok=True)

        years = df["year"].unique() if "year" in df.columns else []
        written_files = []
        for year in years:
            year_df = df[df["year"] == year].drop(columns=["year"])
            file_path = self._kline_file(symbol, int(year))
            table = pa.Table.from_pandas(year_df)
            pq.write_table(table, file_path, compression=self.compression)
            written_files.append(str(file_path))

        if not written_files:
            file_path = self._kline_file(symbol, 0)
            df_to_write = df.drop(columns=["year"]) if "year" in df.columns else df
            table = pa.Table.from_pandas(df_to_write)
            pq.write_table(table, file_path, compression=self.compression)
            written_files.append(str(file_path))

        return str(out_dir)

    def read_kline(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        kline_dir = self._kline_dir(symbol)
        if not kline_dir.exists():
            return pd.DataFrame()

        files = sorted(kline_dir.glob("*.parquet"))
        if not files:
            return pd.DataFrame()

        dfs = []
        for f in files:
            df = pq.read_table(f).to_pandas()
            dfs.append(df)

        result = pd.concat(dfs, ignore_index=True)

        if "trade_date" in result.columns:
            result["trade_date"] = pd.to_datetime(result["trade_date"])
            if start_date:
                result = result[result["trade_date"] >= pd.Timestamp(start_date)]
            if end_date:
                result = result[result["trade_date"] <= pd.Timestamp(end_date)]
            result = result.sort_values("trade_date")

        return result.reset_index(drop=True)

    def list_symbols(self) -> list[str]:
        kline_root = self.base_path / "kline"
        if not kline_root.exists():
            return []
        return [d.name for d in kline_root.iterdir() if d.is_dir()]

    def symbol_date_range(self, symbol: str) -> tuple:
        kline_dir = self._kline_dir(symbol)
        if not kline_dir.exists():
            return (None, None)

        files = sorted(kline_dir.glob("*.parquet"))
        if not files:
            return (None, None)

        all_dates = []
        for f in files:
            df = pq.read_table(f, columns=["trade_date"]).to_pandas()
            all_dates.append(pd.to_datetime(df["trade_date"]))

        dates = pd.concat(all_dates)
        return (dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d"))
