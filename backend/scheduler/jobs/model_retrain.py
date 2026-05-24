import logging
from datetime import date

import numpy as np

from backend.config import AppConfig
from backend.persistence.database import get_session
from backend.persistence.models import Stock
from backend.persistence.parquet_store import ParquetStore
from backend.persistence.repository import Repository
from backend.strategy.layer2_ml.feature_builder import FeatureBuilder
from backend.strategy.layer2_ml.model_trainer import ModelTrainer

logger = logging.getLogger(__name__)


def run_model_retrain(config: AppConfig) -> int:
    session = get_session()
    try:
        stock_repo = Repository(session, Stock)
        stocks = stock_repo.find_by(status="active")
        if len(stocks) < 50:
            logger.warning(f"Not enough stocks for training: {len(stocks)}")
            return 0

        parquet = ParquetStore(
            base_path=config.persistence.parquet.base_path,
            compression=config.persistence.parquet.compression,
        )

        feature_builder = FeatureBuilder(lookback_days=252)
        kline_by_symbol = {}
        for stock in stocks[:500]:
            df = parquet.read_kline(stock.symbol)
            if not df.empty:
                kline_by_symbol[stock.symbol] = df

        if len(kline_by_symbol) < 50:
            logger.warning("Not enough kline data for training")
            return 0

        forward_returns = {}
        for symbol, df in kline_by_symbol.items():
            if "close" in df.columns and len(df) > 20:
                forward_returns[symbol] = df["close"].pct_change(-20).iloc[-20] * 100

        X, y = feature_builder.build_training_matrix(
            kline_by_symbol, {}, {}, forward_returns
        )

        if len(X) < 50:
            logger.warning(f"Not enough feature rows: {len(X)}")
            return 0

        X = X.astype(float)
        y = y.astype(float)

        mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X = X[mask]
        y = y[mask]

        trainer = ModelTrainer(model_dir=config.persistence.models["path"])
        trainer.train(X, y)
        logger.info(f"Model retrained on {len(X)} samples")
        return len(X)
    finally:
        session.close()
