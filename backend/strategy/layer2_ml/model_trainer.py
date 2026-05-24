import logging
import os
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import joblib
import numpy as np

if TYPE_CHECKING:
    from lightgbm import LGBMRegressor

logger = logging.getLogger(__name__)


def _get_lgbm():
    from lightgbm import LGBMRegressor
    return LGBMRegressor


class ModelTrainer:
    def __init__(self, model_dir: str = "data/models"):
        self.model_dir = Path(model_dir)
        if not self.model_dir.is_absolute():
            self.model_dir = Path(__file__).resolve().parent.parent.parent.parent / model_dir
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def train(self, X: np.ndarray, y: np.ndarray):
        LGBMRegressor = _get_lgbm()
        if len(X) < 50:
            logger.warning(f"Not enough training samples: {len(X)}")
            return self._load_latest_model() or self._default_model()

        n_splits = min(3, len(X) // 30)
        if n_splits < 2:
            return self._load_latest_model() or self._default_model()

        from sklearn.model_selection import TimeSeriesSplit
        tscv = TimeSeriesSplit(n_splits=n_splits)

        model = LGBMRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            num_leaves=31,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_alpha=0.1,
            reg_lambda=0.1,
            random_state=42,
            verbose=-1,
        )

        model.fit(X, y)

        self._save_model(model)
        logger.info(f"Model trained on {len(X)} samples, saved to {self.model_dir}")
        return model

    def _save_model(self, model):
        today = date.today().strftime("%Y%m%d")
        path = self.model_dir / f"lgb_model_{today}.pkl"
        joblib.dump(model, path)
        latest = self.model_dir / "lgb_model_latest.pkl"
        joblib.dump(model, latest)

    def _load_latest_model(self):
        latest = self.model_dir / "lgb_model_latest.pkl"
        if latest.exists():
            return joblib.load(latest)
        return None

    def _default_model(self):
        LGBMRegressor = _get_lgbm()
        return LGBMRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=5,
            verbose=-1,
            random_state=42,
        )
