import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class RevenueGrowthFactor(BaseFactor):
    name = "revenue_growth"
    category = "growth"
    depends_on = ["revenue"]

    def compute(self, df: pd.DataFrame, revenue: pd.Series = None) -> pd.Series:
        if revenue is not None:
            rev = revenue.replace(0, np.nan)
            growth = rev.pct_change(periods=4) if isinstance(revenue, pd.Series) else pd.Series(np.nan)
        else:
            growth = pd.Series(np.nan, index=df.index)
        return growth.replace([np.inf, -np.inf], np.nan)


class ProfitGrowthFactor(BaseFactor):
    name = "profit_growth"
    category = "growth"
    depends_on = ["net_profit_parent"]

    def compute(self, df: pd.DataFrame, net_profit: pd.Series = None) -> pd.Series:
        if net_profit is not None:
            profit = net_profit.replace(0, np.nan)
            growth = profit.pct_change(periods=4) if isinstance(net_profit, pd.Series) else pd.Series(np.nan)
        else:
            growth = pd.Series(np.nan, index=df.index)
        return growth.replace([np.inf, -np.inf], np.nan)


class RdRatioFactor(BaseFactor):
    name = "rd_ratio"
    category = "growth"
    depends_on = ["rd_expense", "revenue"]

    def compute(self, df: pd.DataFrame, rd_expense: pd.Series = None, revenue: pd.Series = None) -> pd.Series:
        if rd_expense is not None and revenue is not None:
            ratio = rd_expense / revenue.replace(0, np.nan)
        else:
            ratio = pd.Series(np.nan, index=df.index)
        return ratio.replace([np.inf, -np.inf], np.nan)
