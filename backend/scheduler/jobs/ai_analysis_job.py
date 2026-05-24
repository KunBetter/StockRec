import asyncio
import json
import logging
from datetime import date

from backend.ai.deepseek_client import DeepSeekClient
from backend.ai.financial_analyzer import FinancialAnalyzer
from backend.ai.news_analyzer import NewsAnalyzer
from backend.ai.industry_analyzer import IndustryAnalyzer
from backend.ai.recommendation_writer import RecommendationWriter
from backend.config import AppConfig
from backend.persistence.database import get_session
from backend.persistence.repository import Repository
from backend.persistence.models import Recommendation, FinancialData, Stock

logger = logging.getLogger(__name__)


def run_ai_analysis(config: AppConfig) -> int:
    session = get_session()
    try:
        ai_cfg = config.ai
        if not ai_cfg.api_key:
            logger.warning("DeepSeek API key not configured, skipping AI analysis")
            return 0

        client = DeepSeekClient(
            api_key=ai_cfg.api_key,
            base_url=ai_cfg.base_url,
            model=ai_cfg.model,
            max_tokens=ai_cfg.max_tokens,
            temperature=ai_cfg.temperature,
            max_concurrent=ai_cfg.rate_limit.max_concurrent,
        )

        today = date.today()
        rec_repo = Repository(session, Recommendation)
        stock_repo = Repository(session, Stock)

        # Get today's top recommendations
        recs = rec_repo.find_by(trade_date=today)
        if not recs:
            # Get latest recommendations
            all_recs = session.query(Recommendation).order_by(
                Recommendation.trade_date.desc()
            ).limit(30).all()
            recs = all_recs

        if not recs:
            logger.warning("No recommendations to analyze")
            return 0

        fin_analyzer = FinancialAnalyzer(client)
        news_analyzer = NewsAnalyzer(client)
        ind_analyzer = IndustryAnalyzer(client)
        writer = RecommendationWriter(client)

        async def analyze_one(rec):
            try:
                stock = stock_repo.find_one_by(symbol=rec.symbol)
                stock_name = stock.name if stock else rec.symbol

                # Run analyses concurrently
                fin_task = fin_analyzer.analyze(rec.symbol, stock_name, {})
                news_task = news_analyzer.analyze(rec.symbol, stock_name, [])
                ind_task = ind_analyzer.analyze(
                    rec.symbol, stock_name,
                    industry=stock.industry if stock else "未知",
                )
                fin_result, news_result, ind_result = await asyncio.gather(
                    fin_task, news_task, ind_task
                )

                rec_result = await writer.write(
                    symbol=rec.symbol,
                    stock_name=stock_name,
                    current_price=rec.current_price or 0,
                    composite_score=rec.composite_score or 50,
                    predicted_return=rec.predicted_return or 0,
                    momentum_score=rec.momentum_score or 50,
                    quality_score=rec.quality_score or 50,
                    risk_level=rec.risk_level or "medium",
                    financial_summary=fin_result.get("profit_assessment", ""),
                    news_summary=news_result.get("key_factors", ""),
                    industry_summary=ind_result.get("outlook", ""),
                )

                # Update recommendation with AI content
                rec.ai_summary = rec_result.get("summary", "")
                rec.ai_full_analysis = json.dumps({
                    "financial": fin_result,
                    "news": news_result,
                    "industry": ind_result,
                }, ensure_ascii=False)
                rec.ai_risk_flags = json.dumps(
                    rec_result.get("risk_flags", []), ensure_ascii=False
                )
                rec.sentiment_score = float(news_result.get("sentiment_score", 50)) / 2 + 50

                return True
            except Exception as e:
                logger.error(f"AI analysis failed for {rec.symbol}: {e}")
                return False

        async def run_all():
            tasks = [analyze_one(rec) for rec in recs[:30]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return sum(1 for r in results if r is True)

        processed = asyncio.run(run_all())
        session.commit()
        logger.info(f"AI analysis: {processed} stocks analyzed")
        return processed
    finally:
        session.close()
