import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class Momentum1MFactor(BaseFactor):
    name = "momentum_1m"
    category = "momentum"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        return df["close"].pct_change(periods=20)


class Momentum3MFactor(BaseFactor):
    name = "momentum_3m"
    category = "momentum"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        return df["close"].pct_change(periods=60)


class Momentum12m1mFactor(BaseFactor):
    name = "momentum_12m1m"
    category = "momentum"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        ret_12m = df["close"].pct_change(periods=252)
        ret_1m = df["close"].pct_change(periods=20)
        return ret_12m - ret_1m
