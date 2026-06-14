import logging

from backend.strategy.layer3_events.earnings_surprise import EarningsSurpriseDetector
from backend.strategy.layer3_events.high_dividend import HighDividendDetector
from backend.strategy.layer3_events.buyback_detector import BuybackDetector

logger = logging.getLogger(__name__)


class EventScorer:
    def __init__(self):
        self.earnings = EarningsSurpriseDetector()
        self.dividend = HighDividendDetector()
        self.buyback = BuybackDetector()

    def score(
        self,
        financial_data=None,
        dividend_yield: float = None,
        has_buyback: bool = False,
    ) -> float:
        try:
            earnings_score = self.earnings.detect(financial_data)
        except Exception:
            earnings_score = 0.0
        try:
            dividend_score = self.dividend.detect(dividend_yield)
        except Exception:
            dividend_score = 0.0
        try:
            buyback_score = self.buyback.detect(has_buyback)
        except Exception:
            buyback_score = 0.0

        weights = {"earnings": 0.6, "dividend": 0.3, "buyback": 0.1}
        final = (
            earnings_score * weights["earnings"]
            + dividend_score * weights["dividend"]
            + buyback_score * weights["buyback"]
        )
        return max(0, min(100, final))
