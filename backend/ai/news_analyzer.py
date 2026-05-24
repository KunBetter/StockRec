import json
import logging

from backend.ai.deepseek_client import DeepSeekClient
from backend.ai.prompts import NEWS_SENTIMENT_PROMPT

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    def __init__(self, client: DeepSeekClient):
        self.client = client

    async def analyze(
        self,
        symbol: str,
        stock_name: str,
        news_list: list[dict],
    ) -> dict:
        if not news_list:
            return self._empty_result()

        news_text = "\n".join(
            f"- [{n.get('date', '')}] {n.get('title', '')}"
            for n in news_list[:10]
        )

        prompt = NEWS_SENTIMENT_PROMPT.format(
            stock_name=stock_name,
            symbol=symbol,
            news_list=news_text,
        )

        messages = [
            {"role": "system", "content": "你是专业的A股新闻分析师。"},
            {"role": "user", "content": prompt},
        ]

        response = await self.client.analyze_json(messages)
        if response:
            try:
                return json.loads(response.strip())
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse news sentiment JSON for {symbol}")

        return self._empty_result()

    @staticmethod
    def _empty_result() -> dict:
        return {
            "sentiment_label": "neutral",
            "sentiment_score": 0,
            "key_factors": "暂无近期新闻数据",
        }
