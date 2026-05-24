import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class TurnoverFactor(BaseFactor):
    name = "turnover"
    category = "liquidity"
    depends_on = ["turn_rate"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        if "turn_rate" in df.columns:
            return pd.to_numeric(df["turn_rate"], errors="coerce")
        return pd.Series(np.nan, index=df.index)


class AmihudIlliquidityFactor(BaseFactor):
    name = "amihud_illiquidity"
    category = "liquidity"
    depends_on = ["close", "amount"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        returns = df["close"].pct_change().abs()
        volume = df.get("amount", pd.Series(0, index=df.index)).replace(0, np.nan)
        daily_illiq = returns / volume
        return daily_illiq.rolling(window=20).mean()


class TurnoverChangeFactor(BaseFactor):
    name = "turnover_change"
    category = "liquidity"
    depends_on = ["turn_rate"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        if "turn_rate" in df.columns:
            turnover = pd.to_numeric(df["turn_rate"], errors="coerce")
            short_avg = turnover.rolling(window=20).mean()
            long_avg = turnover.rolling(window=60).mean()
            return short_avg / long_avg.replace(0, np.nan)
        return pd.Series(np.nan, index=df.index)
