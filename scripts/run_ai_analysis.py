#!/usr/bin/env python3
"""Run AI analysis on current recommendations using DeepSeek."""
import sys, os, asyncio, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date
from dotenv import load_dotenv
load_dotenv()

from backend.config import load_config
from backend.persistence.database import get_session, init_db
from backend.persistence.repository import Repository
from backend.persistence.models import Recommendation, Stock
from backend.ai.deepseek_client import DeepSeekClient
from backend.ai.financial_analyzer import FinancialAnalyzer
from backend.ai.news_analyzer import NewsAnalyzer
from backend.ai.industry_analyzer import IndustryAnalyzer
from backend.ai.recommendation_writer import RecommendationWriter

config = load_config()
init_db(config.persistence.database.path)

ai_cfg = config.ai
api_key = os.environ.get("DEEPSEEK_API_KEY", ai_cfg.api_key)
print(f"API Key: {api_key[:20]}...")
print(f"Model: {ai_cfg.model}")
print(f"Base URL: {ai_cfg.base_url}")

client = DeepSeekClient(
    api_key=api_key,
    base_url=ai_cfg.base_url,
    model=ai_cfg.model,
    max_tokens=ai_cfg.max_tokens,
    temperature=ai_cfg.temperature,
    max_concurrent=3,
)

fin_analyzer = FinancialAnalyzer(client)
news_analyzer = NewsAnalyzer(client)
ind_analyzer = IndustryAnalyzer(client)
writer = RecommendationWriter(client)

session = get_session()
today = date.today()

recs = session.query(Recommendation).filter(
    Recommendation.trade_date == today
).order_by(Recommendation.composite_score.desc()).all()

if not recs:
    recs = session.query(Recommendation).order_by(
        Recommendation.trade_date.desc(), Recommendation.composite_score.desc()
    ).all()


stock_repo = Repository(session, Stock)
print(f"\nAnalyzing {len(recs)} stocks with DeepSeek...\n")


async def analyze_one(rec):
    stock = stock_repo.find_one_by(symbol=rec.symbol)
    name = stock.name if stock else rec.symbol

    fin_task = fin_analyzer.analyze(rec.symbol, name, {})
    news_task = news_analyzer.analyze(rec.symbol, name, [])
    ind_task = ind_analyzer.analyze(rec.symbol, name, stock.industry if stock else "未知")
    fin_r, news_r, ind_r = await asyncio.gather(fin_task, news_task, ind_task)

    result = await writer.write(
        symbol=rec.symbol, stock_name=name,
        current_price=rec.current_price or 0,
        composite_score=rec.composite_score or 50,
        predicted_return=rec.predicted_return or 0,
        momentum_score=rec.momentum_score or 50,
        quality_score=rec.quality_score or 50,
        risk_level=rec.risk_level or "medium",
        financial_summary=fin_r.get("profit_assessment", ""),
        news_summary=news_r.get("key_factors", ""),
        industry_summary=ind_r.get("outlook", ""),
    )

    rec.ai_summary = result.get("summary", "")
    rec.ai_full_analysis = json.dumps({
        "financial": fin_r, "news": news_r, "industry": ind_r,
    }, ensure_ascii=False)
    rec.ai_risk_flags = json.dumps(result.get("risk_flags", []), ensure_ascii=False)

    # Derive sentiment from recommendation level + financial score
    rec_level = result.get("recommendation_level", "中性")
    fin_score = float(fin_r.get("overall_score", 50))
    news_sent = float(news_r.get("sentiment_score", 0))
    if news_sent == 0:
        # No news data, derive from recommendation strength
        level_map = {"强烈推荐": 85, "推荐": 70, "中性": 50, "谨慎": 30}
        rec.sentiment_score = level_map.get(rec_level, 50)
    else:
        rec.sentiment_score = min(100, max(0, news_sent / 2 + 50))

    return name, result


async def main():
    tasks = [analyze_one(r) for r in recs]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"  ✗ {recs[i].symbol}: {r}")
        else:
            name, res = r
            print(f"  ✓ {name}({recs[i].symbol})")
            print(f"    摘要: {res.get('summary','')[:80]}...")
            print(f"    建议: {res.get('recommendation_level','')}")
            print(f"    风险: {res.get('risk_flags',[])}")

    session.commit()
    print(f"\nDone! Updated {len(recs)} recommendations with AI analysis.")

asyncio.run(main())
session.close()
