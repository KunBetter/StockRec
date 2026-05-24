import json
import logging
from typing import Optional

from backend.ai.deepseek_client import DeepSeekClient
from backend.ai.prompts import FINANCIAL_REPORT_PROMPT

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    def __init__(self, client: DeepSeekClient):
        self.client = client

    async def analyze(
        self,
        symbol: str,
        stock_name: str,
        financial_data: dict,
    ) -> dict:
        if not financial_data:
            return self._empty_result()

        prompt = FINANCIAL_REPORT_PROMPT.format(
            stock_name=stock_name,
            symbol=symbol,
            revenue=financial_data.get("revenue", "N/A"),
            net_profit=financial_data.get("net_profit_parent", "N/A"),
            eps=financial_data.get("eps", "N/A"),
            roe=f"{financial_data.get('roe', 'N/A')}%",
            total_assets=financial_data.get("total_assets", "N/A"),
            debt_ratio=financial_data.get("debt_ratio", "N/A"),
        )

        messages = [
            {"role": "system", "content": "你是专业的A股财务分析师。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.client.analyze_json(messages)
        if response:
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse financial analysis JSON for {symbol}")

        return self._empty_result()

    @staticmethod
    def _empty_result() -> dict:
        return {
            "profit_assessment": "暂无足够数据进行分析",
            "growth_assessment": "暂无足够数据进行分析",
            "health_assessment": "暂无足够数据进行分析",
            "overall_score": 50,
        }
