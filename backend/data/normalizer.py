import pandas as pd

COLUMN_MAP = {
    "date": "trade_date",
    "trade_date": "trade_date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "preclose": "preclose",
    "volume": "volume",
    "amount": "amount",
    "pctChg": "pct_change",
    "pct_change": "pct_change",
    "turn": "turn_rate",
    "turn_rate": "turn_rate",
    "adjustflag": "adjust_flag",
    "tradestatus": "trade_status",
}


def normalize_kline(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Drop 'date' if 'trade_date' already exists to avoid duplicate column after rename
    if "trade_date" in df.columns and "date" in df.columns:
        df = df.drop(columns=["date"])

    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})

    # Deduplicate columns that may exist from both source and rename
    df = df.loc[:, ~df.columns.duplicated()]

    if "trade_date" in df.columns:
        df["trade_date"] = pd.to_datetime(df["trade_date"])

    numeric_cols = ["open", "high", "low", "close", "preclose", "volume", "amount", "pct_change", "turn_rate"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "symbol" not in df.columns:
        df["symbol"] = symbol

    return df


def normalize_realtime(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    for col in ["price", "open", "high", "low", "preclose", "pct_change", "volume", "amount", "market_cap"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
