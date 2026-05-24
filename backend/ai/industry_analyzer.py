import json
import logging

from backend.ai.deepseek_client import DeepSeekClient
from backend.ai.prompts import INDUSTRY_OUTLOOK_PROMPT

logger = logging.getLogger(__name__)


class IndustryAnalyzer:
    def __init__(self, client: DeepSeekClient):
        self.client = client

    async def analyze(
        self,
        symbol: str,
        stock_name: str,
        industry: str = "未知行业",
        context: str = "",
    ) -> dict:
        prompt = INDUSTRY_OUTLOOK_PROMPT.format(
            industry=industry,
            stock_name=stock_name,
            symbol=symbol,
            industry_context=context or "暂无行业动态信息",
        )

        messages = [
            {"role": "system", "content": "你是专业的A股行业分析师。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.client.analyze_json(messages)
        if response:
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse industry analysis JSON for {symbol}")

        return self._empty_result()

    @staticmethod
    def _empty_result() -> dict:
        return {
            "prosperity": "中",
            "outlook": "暂无足够数据判断行业趋势",
            "competitive_position": "暂无竞争分析数据",
        }
