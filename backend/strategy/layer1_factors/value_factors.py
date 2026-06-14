import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class EPFactor(BaseFactor):
    name = "ep"
    category = "value"
    depends_on = ["close", "market_cap", "net_profit_parent"]

    def compute(self, df: pd.DataFrame, market_cap: pd.Series = None, net_profit: pd.Series = None, **kwargs) -> pd.Series:
        if net_profit is not None and market_cap is not None:
            ep = net_profit / market_cap
        else:
            ep = pd.Series(np.nan, index=df.index)
        return ep.replace([np.inf, -np.inf], np.nan)


class BPFactor(BaseFactor):
    name = "bp"
    category = "value"
    depends_on = ["close", "market_cap", "net_assets"]

    def compute(self, df: pd.DataFrame, market_cap: pd.Series = None, net_assets: pd.Series = None, **kwargs) -> pd.Series:
        if net_assets is not None and market_cap is not None:
            bp = net_assets / market_cap
        else:
            bp = pd.Series(np.nan, index=df.index)
        return bp.replace([np.inf, -np.inf], np.nan)


class SPFactor(BaseFactor):
    name = "sp"
    category = "value"
    depends_on = ["close", "market_cap", "revenue"]

    def compute(self, df: pd.DataFrame, market_cap: pd.Series = None, revenue: pd.Series = None, **kwargs) -> pd.Series:
        if revenue is not None and market_cap is not None:
            sp = revenue / market_cap
        else:
            sp = pd.Series(np.nan, index=df.index)
        return sp.replace([np.inf, -np.inf], np.nan)


class DividendYieldFactor(BaseFactor):
    name = "dividend_yield"
    category = "value"
    depends_on = ["close"]

    def compute(self, df: pd.DataFrame, **kwargs) -> pd.Series:
        df["pct_change"] = pd.to_numeric(df.get("pct_change", 0), errors="coerce")
        return df["pct_change"].rolling(window=252, min_periods=20).apply(
            lambda x: (x > 0).sum() / len(x) * x.mean() if len(x) > 0 else np.nan
        )
