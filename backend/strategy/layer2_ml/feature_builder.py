import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class FeatureBuilder:
    def __init__(self, lookback_days: int = 252):
        self.lookback_days = lookback_days

    def build_features(
        self,
        kline_df: pd.DataFrame,
        financial_data: dict = None,
        fund_flow_data: dict = None,
    ) -> pd.DataFrame:
        if kline_df.empty:
            return pd.DataFrame()

        df = kline_df.sort_values("trade_date").tail(self.lookback_days).copy()

        features = pd.DataFrame(index=df.index[-1:])

        if "close" in df.columns:
            returns = df["close"].pct_change()
            features["ret_1d"] = returns.iloc[-1] if not returns.empty else np.nan
            features["ret_5d"] = df["close"].pct_change(5).iloc[-1]
            features["ret_10d"] = df["close"].pct_change(10).iloc[-1]
            features["ret_20d"] = df["close"].pct_change(20).iloc[-1]
            features["ret_60d"] = df["close"].pct_change(60).iloc[-1]
            features["vol_20d"] = returns.rolling(20).std().iloc[-1]
            features["max_dd_20d"] = (df["close"] / df["close"].rolling(20).max() - 1).min()

        if "volume" in df.columns:
            features["vol_5d_avg"] = df["volume"].tail(5).mean()
            features["vol_20d_avg"] = df["volume"].tail(20).mean()
            features["vol_ratio"] = features["vol_5d_avg"] / features["vol_20d_avg"].replace(0, np.nan)

        if "turn_rate" in df.columns:
            features["turn_rate"] = pd.to_numeric(df["turn_rate"].iloc[-1], errors="coerce")

        if "amount" in df.columns:
            features["amount_20d_avg"] = df["amount"].tail(20).mean()

        if financial_data:
            for key in ["revenue", "net_profit_parent", "net_assets", "total_assets", "roe", "eps"]:
                if key in financial_data:
                    features[f"fin_{key}"] = financial_data[key]

        if fund_flow_data:
            for key in ["main_net_inflow", "northbound_pct", "margin_balance"]:
                if key in fund_flow_data:
                    features[f"flow_{key}"] = fund_flow_data[key]

        return features.fillna(0)

    def build_training_matrix(
        self,
        kline_by_symbol: dict[str, pd.DataFrame],
        financials_by_symbol: dict[str, dict],
        fund_flows_by_symbol: dict[str, dict],
        forward_returns: dict[str, float],
    ) -> tuple[np.ndarray, np.ndarray]:
        X_list = []
        y_list = []
        for symbol, df in kline_by_symbol.items():
            if symbol not in forward_returns:
                continue
            fin = financials_by_symbol.get(symbol, {})
            flow = fund_flows_by_symbol.get(symbol, {})
            features = self.build_features(df, fin, flow)
            if features.empty or len(features.columns) == 0:
                continue
            X_list.append(features.iloc[0].values)
            y_list.append(forward_returns[symbol])

        if not X_list:
            return np.array([]), np.array([])
        return np.array(X_list), np.array(y_list)
