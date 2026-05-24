class CompositeScorer:
    def __init__(self, weights: dict = None):
        self.weights = weights or {
            "predicted_return": 0.5,
            "momentum_score": 0.2,
            "quality_score": 0.2,
            "sentiment_score": 0.1,
        }

    def compute(
        self,
        predicted_return: float = 0,
        momentum_score: float = 50,
        quality_score: float = 50,
        sentiment_score: float = 50,
    ) -> float:
        score = (
            predicted_return * self.weights["predicted_return"]
            + momentum_score * self.weights["momentum_score"]
            + quality_score * self.weights["quality_score"]
            + sentiment_score * self.weights["sentiment_score"]
        )
        return max(0, min(100, score))


class RiskClassifier:
    def __init__(self, low_threshold: int = 30, medium_threshold: int = 60):
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold

    def classify(self, risk_score: float) -> str:
        if risk_score <= self.low_threshold:
            return "low"
        elif risk_score <= self.medium_threshold:
            return "medium"
        return "high"

    def compute_risk_score(
        self,
        volatility: float = 0,
        max_drawdown: float = 0,
        leverage: float = 0,
        market_cap: float = 0,
    ) -> float:
        # Volatility score: higher vol = higher risk
        vol_score = min(100, volatility * 250)

        # Drawdown score
        dd_score = abs(max_drawdown) * 100 if max_drawdown else 0

        # Leverage score
        leverage_score = min(100, max(0, (leverage - 0.3) * 100))

        # Size score: smaller cap = higher risk
        size_score = max(0, 100 - market_cap / 1e11 * 100) if market_cap > 0 else 100

        risk = vol_score * 0.3 + dd_score * 0.2 + leverage_score * 0.15 + size_score * 0.15
        return max(0, min(100, risk))
