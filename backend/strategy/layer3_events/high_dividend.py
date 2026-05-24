import logging

logger = logging.getLogger(__name__)


class HighDividendDetector:
    def detect(self, dividend_yield: float = None) -> float:
        if dividend_yield is None:
            return 0.0
        if dividend_yield > 6:
            return 90.0
        elif dividend_yield > 4:
            return 60.0
        elif dividend_yield > 2:
            return 30.0
        return 0.0
