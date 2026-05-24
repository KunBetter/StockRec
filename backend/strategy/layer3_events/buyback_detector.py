import logging

logger = logging.getLogger(__name__)


class BuybackDetector:
    def detect(self, has_buyback: bool = False) -> float:
        return 80.0 if has_buyback else 0.0
