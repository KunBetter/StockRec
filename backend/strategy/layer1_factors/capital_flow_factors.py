import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class MajorInflowFactor(BaseFactor):
    name = "major_inflow"
    category = "capital_flow"
    depends_on = ["main_net_inflow"]

    def compute(self, df: pd.DataFrame, main_net_inflow: pd.Series = None, **kwargs) -> pd.Series:
        if main_net_inflow is not None:
            return main_net_inflow.rolling(window=10).sum()
        return pd.Series(np.nan, index=df.index)


class NorthboundPctFactor(BaseFactor):
    name = "northbound_pct"
    category = "capital_flow"
    depends_on = ["northbound_pct"]

    def compute(self, df: pd.DataFrame, northbound_pct: pd.Series = None, **kwargs) -> pd.Series:
        if northbound_pct is not None:
            return northbound_pct
        return pd.Series(np.nan, index=df.index)


class MarginChangeFactor(BaseFactor):
    name = "margin_change"
    category = "capital_flow"
    depends_on = ["margin_balance"]

    def compute(self, df: pd.DataFrame, margin_balance: pd.Series = None, **kwargs) -> pd.Series:
        if margin_balance is not None:
            return margin_balance.pct_change(periods=20)
        return pd.Series(np.nan, index=df.index)
