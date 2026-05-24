import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class HistoricalVolatilityFactor(BaseFactor):
    name = "historical_volatility"
    category = "volatility"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        returns = df["close"].pct_change()
        return returns.rolling(window=20).std() * np.sqrt(252)


class DownsideVolatilityFactor(BaseFactor):
    name = "downside_volatility"
    category = "volatility"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        returns = df["close"].pct_change()
        downside = returns[returns < 0]
        return downside.rolling(window=20, min_periods=5).std().reindex(returns.index) * np.sqrt(252)
