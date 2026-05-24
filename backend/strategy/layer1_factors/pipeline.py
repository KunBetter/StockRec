import logging
from datetime import date, datetime

import numpy as np
import pandas as pd

from backend.strategy.layer1_factors.registry import ALL_FACTORS, get_factor

logger = logging.getLogger(__name__)


class FactorPipeline:
    def __init__(self, config):
        self.config = config
        self.factors = ALL_FACTORS

    def compute_all_factors(
        self,
        kline_df: pd.DataFrame,
        financials: dict = None,
        fund_flows: dict = None,
    ) -> dict[str, float]:
        if kline_df.empty:
            return {}

        df = kline_df.sort_values("trade_date").copy()
        financials = financials or {}
        fund_flows = fund_flows or {}

        results = {}
        for factor in self.factors:
            try:
                extra_kwargs = self._build_kwargs(factor, df, financials, fund_flows)
                raw = factor.compute(df, **extra_kwargs)
                if isinstance(raw, pd.Series) and not raw.empty:
                    value = raw.iloc[-1]
                    if pd.notna(value):
                        results[factor.name] = float(value)
            except Exception as e:
                logger.warning(f"Factor {factor.name} computation failed: {e}")

        return results

    def _build_kwargs(self, factor, df, financials, fund_flows):
        kwargs = {}
        if factor.category == "value":
            kwargs["market_cap"] = financials.get("market_cap")
            kwargs["net_profit"] = financials.get("net_profit_parent")
            kwargs["net_assets"] = financials.get("net_assets")
            kwargs["revenue"] = financials.get("revenue")
        elif factor.category == "quality":
            kwargs["net_profit"] = financials.get("net_profit_parent")
            kwargs["net_assets"] = financials.get("net_assets")
            kwargs["total_assets"] = financials.get("total_assets")
            kwargs["revenue"] = financials.get("revenue")
            kwargs["operating_cost"] = financials.get("operating_cost")
        elif factor.category == "growth":
            kwargs["revenue"] = financials.get("revenue_series")
            kwargs["net_profit"] = financials.get("net_profit_series")
            kwargs["rd_expense"] = financials.get("rd_expense")
        elif factor.category == "capital_flow":
            kwargs["main_net_inflow"] = fund_flows.get("main_net_inflow")
            kwargs["northbound_pct"] = fund_flows.get("northbound_pct")
            kwargs["margin_balance"] = fund_flows.get("margin_balance")
        return kwargs

    def cross_sectional_normalize(
        self, all_factor_values: dict[str, dict[str, float]]
    ) -> dict[str, dict[str, dict[str, float]]]:
        factor_names = set()
        for symbol, factors in all_factor_values.items():
            factor_names.update(factors.keys())

        result: dict[str, dict[str, dict]] = {}
        for fname in factor_names:
            values = []
            symbols_with_factor = []
            for symbol, factors in all_factor_values.items():
                if fname in factors:
                    symbols_with_factor.append(symbol)
                    values.append(factors[fname])

            if len(values) < 2:
                continue

            arr = np.array(values, dtype=float)
            mean = np.nanmean(arr)
            std = np.nanstd(arr)
            if std == 0 or np.isnan(std):
                continue

            z_scores = (arr - mean) / std
            z_scores = np.clip(z_scores, -3, 3)

            for i, symbol in enumerate(symbols_with_factor):
                if symbol not in result:
                    result[symbol] = {}
                percentile = (np.sum(arr <= arr[i])) / len(arr)
                result[symbol][fname] = {
                    "raw_value": arr[i],
                    "z_score": float(z_scores[i]),
                    "percentile": float(percentile),
                }

        return result

    def compute_composite_score(
        self,
        normalized_factors: dict[str, dict[str, dict]],
        factor_icirs: dict[str, float] = None,
    ) -> float:
        weights = {}
        if factor_icirs:
            positive_icirs = {k: v for k, v in factor_icirs.items() if v > 0}
            total = sum(positive_icirs.values())
            if total > 0:
                weights = {k: v / total for k, v in positive_icirs.items()}

        total_score = 0.0
        total_weight = 0.0
        for fname, info in normalized_factors.items():
            w = weights.get(fname, 1.0 / len(normalized_factors)) if normalized_factors else 0
            z = info.get("z_score", 0)
            total_score += z * w
            total_weight += w

        if total_weight > 0:
            total_score /= total_weight

        # Scale to 0-100 using cumulative normal-like scaling
        scaled = (total_score + 3) / 6 * 100
        return max(0, min(100, scaled))
