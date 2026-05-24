import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from backend.strategy.layer2_ml.feature_builder import FeatureBuilder

logger = logging.getLogger(__name__)


class ModelPredictor:
    def __init__(self, model_dir: str = "data/models"):
        self.model_dir = Path(model_dir)
        if not self.model_dir.is_absolute():
            self.model_dir = Path(__file__).resolve().parent.parent.parent.parent / model_dir
        self.feature_builder = FeatureBuilder()

    def _load_model(self):
        latest = self.model_dir / "lgb_model_latest.pkl"
        if latest.exists():
            return joblib.load(latest)
        return None

    def predict(
        self,
        kline_df: pd.DataFrame,
        financial_data: dict = None,
        fund_flow_data: dict = None,
    ) -> float:
        model = self._load_model()
        if model is None:
            return 50.0

        features = self.feature_builder.build_features(kline_df, financial_data, fund_flow_data)
        if features.empty:
            return 50.0

        X = features.iloc[0].values.reshape(1, -1)
        pred = float(model.predict(X)[0])

        # Scale prediction to 0-100 score
        scaled = 50 + pred * 10
        return max(0, min(100, scaled))

    def batch_predict(
        self,
        kline_by_symbol: dict[str, pd.DataFrame],
        financials_by_symbol: dict[str, dict],
        fund_flows_by_symbol: dict[str, dict],
    ) -> dict[str, float]:
        results = {}
        for symbol, df in kline_by_symbol.items():
            fin = financials_by_symbol.get(symbol, {})
            flow = fund_flows_by_symbol.get(symbol, {})
            results[symbol] = self.predict(df, fin, flow)
        return results
