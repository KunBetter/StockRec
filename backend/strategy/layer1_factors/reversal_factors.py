import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class WeeklyReversalFactor(BaseFactor):
    name = "weekly_reversal"
    category = "reversal"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        return df["close"].pct_change(periods=5)


class IntradayReversalFactor(BaseFactor):
    name = "intraday_reversal"
    category = "reversal"
    depends_on = ["open", "close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        if "open" not in df.columns:
            return pd.Series(0.0, index=df.index)
        return (df["close"] - df["open"]) / df["open"].replace(0, None)
