import logging

import pandas as pd

logger = logging.getLogger(__name__)


class EarningsSurpriseDetector:
    def detect(self, financial_data: pd.DataFrame = None) -> float:
        if financial_data is None or financial_data.empty:
            return 0.0

        if "net_profit_parent" not in financial_data.columns:
            return 0.0

        profits = financial_data["net_profit_parent"].dropna()
        if len(profits) < 2:
            return 0.0

        latest = profits.iloc[-1]
        previous = profits.iloc[-2]
        if previous == 0:
            return 0.0

        growth = (latest - previous) / abs(previous)
        if growth > 0.5:
            return 90.0
        elif growth > 0.3:
            return 70.0
        elif growth > 0.2:
            return 50.0
        elif growth > 0.1:
            return 30.0
        elif growth > 0:
            return 15.0
        return 0.0
