import logging
from datetime import date, datetime
from typing import Optional

import pandas as pd

from backend.config import AppConfig
from backend.persistence.database import get_session
from backend.persistence.models import FactorScore, Recommendation, Stock, FundFlow, FinancialData
from backend.persistence.parquet_store import ParquetStore
from backend.persistence.repository import Repository
from backend.strategy.layer1_factors.pipeline import FactorPipeline
from backend.strategy.layer2_ml.model_predictor import ModelPredictor
from backend.strategy.layer3_events.event_scorer import EventScorer
from backend.strategy.utils.filter import filter_by_universe, filter_stocks
from backend.strategy.utils.neutralizer import neutralize_industry, neutralize_market_cap
from backend.strategy.utils.scorer import CompositeScorer, RiskClassifier

logger = logging.getLogger(__name__)


class StrategyEngine:
    def __init__(self, config: AppConfig):
        self.config = config
        self.factor_pipeline = FactorPipeline(config)
        self.ml_predictor = ModelPredictor(config.persistence.models["path"])
        self.event_scorer = EventScorer()
        self.composite_scorer = CompositeScorer(
            weights=config.strategy.composite_score_weights.model_dump()
        )
        self.risk_classifier = RiskClassifier(
            low_threshold=config.strategy.risk_classification.low_threshold,
            medium_threshold=config.strategy.risk_classification.medium_threshold,
        )
        self.parquet = ParquetStore(
            base_path=config.persistence.parquet.base_path,
            compression=config.persistence.parquet.compression,
        )

    def run(self, target_date: Optional[date] = None) -> list[dict]:
        target_date = target_date or date.today()

        session = get_session()
        try:
            stock_repo = Repository(session, Stock)
            fin_repo = Repository(session, FinancialData)
            flow_repo = Repository(session, FundFlow)

            stocks = stock_repo.find_by(status="active")
            if not stocks:
                logger.error("No active stocks in database")
                return []

            stocks = filter_by_universe(
                pd.DataFrame([{"symbol": s.symbol, "name": s.name, "market_cap": s.market_cap} for s in stocks]),
                universe=self.config.strategy.stock_universe,
            )
            symbol_list = stocks["symbol"].tolist()
            logger.info(f"Strategy engine: {len(symbol_list)} stocks in universe")

            all_factor_values = {}
            all_scores = {}
            kline_by_symbol = {}
            fin_by_symbol = {}
            flow_by_symbol = {}

            for symbol in symbol_list:
                kline_df = self.parquet.read_kline(symbol)
                if kline_df.empty:
                    continue
                kline_by_symbol[symbol] = kline_df.sort_values("trade_date")

                # Map stock to DB ID for financial/flow lookups
                stock = next((s for s in stocks if hasattr(s, 'symbol')
                             and getattr(s, 'symbol', None) == symbol), None)

            # Layer 1: Factor scores
            all_normalized = {}
            for symbol, df in kline_by_symbol.items():
                factor_values = self.factor_pipeline.compute_all_factors(df)
                all_factor_values[symbol] = factor_values

            normalized = self.factor_pipeline.cross_sectional_normalize(all_factor_values)

            for symbol, factors in normalized.items():
                layer1_score = self.factor_pipeline.compute_composite_score(factors)
                all_scores[symbol] = {"layer1_factor": layer1_score}

                # Store factor scores
                factor_repo = Repository(session, FactorScore)
                for fname, info in factors.items():
                    factor_repo.create(
                        symbol=symbol,
                        calc_date=target_date,
                        factor_name=fname,
                        raw_value=info.get("raw_value"),
                        z_score=info.get("z_score"),
                        percentile=info.get("percentile"),
                    )

            # Layer 2: ML predictions
            for symbol in symbol_list:
                df = kline_by_symbol.get(symbol)
                if df is None:
                    continue
                ml_score = self.ml_predictor.predict(df)
                if symbol not in all_scores:
                    all_scores[symbol] = {}
                all_scores[symbol]["layer2_ml"] = ml_score

            # Layer 3: Event scores
            for symbol in symbol_list:
                event_score = self.event_scorer.score()
                if symbol not in all_scores:
                    all_scores[symbol] = {}
                all_scores[symbol]["layer3_event"] = event_score

            # Merge and composite scoring
            rec_repo = Repository(session, Recommendation)
            recommendations = []

            for symbol in symbol_list:
                scores = all_scores.get(symbol, {})
                if not scores:
                    continue

                l1 = scores.get("layer1_factor", 50)
                l2 = scores.get("layer2_ml", 50)
                l3 = scores.get("layer3_event", 0)

                lw = self.config.strategy.layer_weights
                merged = l1 * lw.layer1_factor + l2 * lw.layer2_ml + l3 * lw.layer3_event

                df = kline_by_symbol.get(symbol)
                current_price = float(df["close"].iloc[-1]) if df is not None and not df.empty else 0

                momentum = self._compute_momentum_score(df) if df is not None else 50
                quality = scores.get("layer1_factor", 50)
                predicted_ret = merged / 100 * 20 - 5  # scale to -5% to +15% range

                # Try to get existing sentiment score from prior AI analysis
                sentiment = 50
                try:
                    existing_rec = rec_repo.find_one_by(symbol=symbol, trade_date=target_date)
                    if existing_rec and existing_rec.sentiment_score is not None:
                        sentiment = existing_rec.sentiment_score
                except Exception:
                    pass

                composite = self.composite_scorer.compute(
                    predicted_return=predicted_ret,
                    momentum_score=momentum,
                    quality_score=quality,
                    sentiment_score=sentiment,
                )

                risk = self.risk_classifier.compute_risk_score(
                    volatility=self._compute_volatility(df) if df is not None else 0,
                    market_cap=float(next(
                        (s.market_cap for s in stocks if hasattr(s, 'symbol')
                         and getattr(s, 'symbol', None) == symbol), 1e10
                    )),
                )
                risk_level = self.risk_classifier.classify(risk)

                rec_data = {
                    "symbol": symbol,
                    "trade_date": target_date,
                    "layer1_factor_score": l1,
                    "layer2_ml_score": l2,
                    "layer3_event_score": l3,
                    "predicted_return": predicted_ret,
                    "momentum_score": momentum,
                    "quality_score": quality,
                    "sentiment_score": sentiment,
                    "composite_score": composite,
                    "risk_level": risk_level,
                    "risk_score": risk,
                    "current_price": current_price,
                }

                # Preserve existing AI analysis data
                existing_rec = rec_repo.find_one_by(symbol=symbol, trade_date=target_date)
                if existing_rec:
                    if existing_rec.ai_summary:
                        rec_data["ai_summary"] = existing_rec.ai_summary
                    if existing_rec.ai_full_analysis:
                        rec_data["ai_full_analysis"] = existing_rec.ai_full_analysis
                    if existing_rec.ai_risk_flags:
                        rec_data["ai_risk_flags"] = existing_rec.ai_risk_flags
                    if existing_rec.sentiment_score and existing_rec.sentiment_score != 50:
                        rec_data["sentiment_score"] = existing_rec.sentiment_score

                rec_repo.upsert(
                    unique_keys={"symbol": symbol, "trade_date": target_date},
                    data=rec_data,
                )

                stock = next((s for s in stocks if hasattr(s, 'symbol')
                             and getattr(s, 'symbol', None) == symbol), None)
                recommendations.append({
                    **rec_data,
                    "name": stock.name if stock and hasattr(stock, 'name') else symbol,
                })

            session.commit()

            # Sort by composite score and take top N
            recommendations.sort(key=lambda x: x["composite_score"], reverse=True)
            top_n = self.config.strategy.output.top_n
            selected = recommendations[:top_n]

            # Assign ranks
            for i, rec in enumerate(selected):
                rec_repo.upsert(
                    unique_keys={"symbol": rec["symbol"], "trade_date": target_date},
                    data={"rank": i + 1},
                )
            session.commit()

            logger.info(f"Strategy engine: {len(selected)} recommendations generated")
            return selected

        finally:
            session.close()

    def _compute_momentum_score(self, df: pd.DataFrame) -> float:
        if df is None or df.empty or "close" not in df.columns:
            return 50
        returns = df["close"].pct_change(20).iloc[-1]
        momentum = (returns * 100 + 10) / 20 * 100
        return max(0, min(100, momentum)) if pd.notna(returns) else 50

    def _compute_volatility(self, df: pd.DataFrame) -> float:
        if df is None or df.empty or "close" not in df.columns:
            return 0
        return df["close"].pct_change().std() if len(df) > 1 else 0
