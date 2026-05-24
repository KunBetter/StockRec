import json
import logging

from backend.ai.deepseek_client import DeepSeekClient
from backend.ai.prompts import COMPREHENSIVE_RECOMMENDATION_PROMPT

logger = logging.getLogger(__name__)


class RecommendationWriter:
    def __init__(self, client: DeepSeekClient):
        self.client = client

    async def write(
        self,
        symbol: str,
        stock_name: str,
        current_price: float,
        composite_score: float,
        predicted_return: float,
        momentum_score: float,
        quality_score: float,
        risk_level: str,
        financial_summary: str = "",
        news_summary: str = "",
        industry_summary: str = "",
    ) -> dict:
        prompt = COMPREHENSIVE_RECOMMENDATION_PROMPT.format(
            stock_name=stock_name,
            symbol=symbol,
            current_price=current_price,
            financial_summary=financial_summary or "暂无财务分析数据",
            news_summary=news_summary or "暂无新闻分析数据",
            industry_summary=industry_summary or "暂无行业分析数据",
            composite_score=f"{composite_score:.1f}",
            predicted_return=f"{predicted_return:.1f}",
            momentum_score=f"{momentum_score:.1f}",
            quality_score=f"{quality_score:.1f}",
            risk_level=risk_level,
        )

        messages = [
            {"role": "system", "content": "你是专业的A股投资顾问，给出简洁、客观的建议。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.client.analyze_json(messages)
        if response:
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse recommendation JSON for {symbol}")

        return self._empty_result()

    @staticmethod
    def _empty_result() -> dict:
        return {
            "summary": "暂无足够数据生成投资建议",
            "risk_flags": ["数据不足，无法充分评估风险"],
            "recommendation_level": "中性",
        }
