import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.base_factor import BaseFactor


class ROEFactor(BaseFactor):
    name = "roe"
    category = "quality"
    depends_on = ["net_profit_parent", "net_assets"]

    def compute(self, df: pd.DataFrame, net_profit: pd.Series = None, net_assets: pd.Series = None) -> pd.Series:
        if net_profit is not None and net_assets is not None:
            roe = net_profit / net_assets.replace(0, np.nan)
        else:
            roe = pd.Series(np.nan, index=df.index)
        return roe.replace([np.inf, -np.inf], np.nan)


class ROAFactor(BaseFactor):
    name = "roa"
    category = "quality"
    depends_on = ["net_profit_parent", "total_assets"]

    def compute(self, df: pd.DataFrame, net_profit: pd.Series = None, total_assets: pd.Series = None) -> pd.Series:
        if net_profit is not None and total_assets is not None:
            roa = net_profit / total_assets.replace(0, np.nan)
        else:
            roa = pd.Series(np.nan, index=df.index)
        return roa.replace([np.inf, -np.inf], np.nan)


class GrossMarginFactor(BaseFactor):
    name = "gross_margin"
    category = "quality"
    depends_on = ["revenue", "operating_cost"]

    def compute(self, df: pd.DataFrame, revenue: pd.Series = None, operating_cost: pd.Series = None) -> pd.Series:
        if revenue is not None and operating_cost is not None:
            margin = (revenue - operating_cost) / revenue.replace(0, np.nan)
        else:
            margin = pd.Series(np.nan, index=df.index)
        return margin.replace([np.inf, -np.inf], np.nan)


class AssetTurnoverFactor(BaseFactor):
    name = "asset_turnover"
    category = "quality"
    depends_on = ["revenue", "total_assets"]

    def compute(self, df: pd.DataFrame, revenue: pd.Series = None, total_assets: pd.Series = None) -> pd.Series:
        if revenue is not None and total_assets is not None:
            turnover = revenue / total_assets.replace(0, np.nan)
        else:
            turnover = pd.Series(np.nan, index=df.index)
        return turnover.replace([np.inf, -np.inf], np.nan)
