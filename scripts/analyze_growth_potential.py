#!/usr/bin/env python3
"""
Comprehensive A-share growth potential analysis by price range.
Screens stocks with 2x+ potential in 3 years using quant strategy + DeepSeek AI.
"""
import sys, os, asyncio, json, time
from datetime import date, datetime
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv()

from backend.config import load_config
from backend.persistence.database import get_session, init_db
from backend.persistence.models import Stock, Recommendation
from backend.ai.deepseek_client import DeepSeekClient
from sqlalchemy import func

import pandas as pd
import logging
logging.basicConfig(level=logging.WARNING)

config = load_config()
init_db(config.persistence.database.path)
session = get_session()

# ── Price ranges ──────────────────────────────────────────────────
PRICE_RANGES = [
    ("<20", 0, 20),
    ("20-50", 20, 50),
    ("50-100", 50, 100),
    ("100-200", 100, 200),
    ("200-300", 200, 300),
    ("300-1000", 300, 1000),
    ("1000+", 1000, 999999),
]

# ── Step 1: Fetch recommendations ─────────────────────────────────
latest = session.query(func.max(Recommendation.trade_date)).scalar()
print(f"📊 Latest recommendation date: {latest}")

all_recs = session.query(Recommendation).filter(
    Recommendation.trade_date == latest,
    Recommendation.current_price > 0
).all()

print(f"📊 Total recommendations: {len(all_recs)}")

# ── Step 2: Enrich with Stock data ─────────────────────────────────
stock_map = {}
for s in session.query(Stock).filter(Stock.status == "active").all():
    stock_map[s.symbol] = s

# ── Step 3: Enrich with akshare real-time fundamentals ────────────
print("\n📡 Fetching real-time fundamentals from akshare...")
try:
    import akshare as ak
    spot_df = ak.stock_zh_a_spot_em()
    spot_df["symbol"] = spot_df["代码"].apply(
        lambda c: f"sh.{c}" if c.startswith(("6", "9")) else f"sz.{c}"
    )
    spot_lookup = {}
    for _, row in spot_df.iterrows():
        spot_lookup[row["symbol"]] = {
            "price": float(row["最新价"]) if pd.notna(row["最新价"]) else None,
            "pe_dynamic": float(row["市盈率-动态"]) if pd.notna(row["市盈率-动态"]) else None,
            "pb": float(row["市净率"]) if pd.notna(row["市净率"]) else None,
            "market_cap": float(row["总市值"]) if pd.notna(row["总市值"]) else None,
            "float_cap": float(row["流通市值"]) if pd.notna(row["流通市值"]) else None,
            "pct_change": float(row["涨跌幅"]) if pd.notna(row["涨跌幅"]) else None,
            "volume": float(row["成交量"]) if pd.notna(row["成交量"]) else None,
            "amount": float(row["成交额"]) if pd.notna(row["成交额"]) else None,
            "turn_rate": float(row["换手率"]) if pd.notna(row["换手率"]) else None,
        }
    print(f"   AKShare spot data: {len(spot_lookup)} stocks")
except Exception as e:
    print(f"   ⚠️  AKShare failed: {e}, using DB data only")
    spot_lookup = {}

# ── Step 4: Build enriched stock list by price range ──────────────
enriched = []
for rec in all_recs:
    stock = stock_map.get(rec.symbol)
    if not stock:
        continue
    # Skip ST and delisted
    name = stock.name or ""
    if stock.is_st or "ST" in name or "退市" in name or "*ST" in name:
        continue

    spot = spot_lookup.get(rec.symbol, {})

    price = rec.current_price or spot.get("price") or 0
    if price <= 0:
        continue

    pe = stock.pe_ttm or spot.get("pe_dynamic")
    pb = stock.pb or spot.get("pb")
    mkt_cap = stock.market_cap or spot.get("market_cap")
    roe = stock.roe

    # Enrich PE/ROE with spot data if DB is missing
    if not pe:
        pe = stock.pe_ttm  # already None if not in DB

    entry = {
        "symbol": rec.symbol,
        "name": name,
        "price": price,
        "composite": rec.composite_score or 50,
        "pred_ret": rec.predicted_return or 0,
        "momentum": rec.momentum_score or 50,
        "quality": rec.quality_score or 50,
        "sentiment": rec.sentiment_score or 50,
        "risk": rec.risk_level or "medium",
        "risk_score": rec.risk_score or 50,
        "holding": rec.holding_period or "中短期",
        "industry": stock.industry or "未知",
        "pe": pe,
        "pb": pb,
        "roe": roe,
        "dividend": stock.dividend_yield,
        "market_cap": mkt_cap,
        "price_change": rec.price_change_pct,
        "ai_summary": rec.ai_summary,
        "ai_risk": rec.ai_risk_flags,
        "turn_rate": spot.get("turn_rate"),
    }
    enriched.append(entry)

print(f"✅ Enriched stocks (clean): {len(enriched)}")

# ── Step 5: Group by price range and rank ─────────────────────────
def compute_growth_score(e):
    """Compute a growth potential score combining quant + fundamentals."""
    score = 0
    # Composite score contributes 40%
    score += (e["composite"] / 100) * 40
    # Momentum contributes 15%
    score += (e["momentum"] / 100) * 15
    # Quality contributes 15%
    score += (e["quality"] / 100) * 15
    # Sentiment contributes 10%
    score += (e["sentiment"] / 100) * 10
    # PE bonus: lower PE = more room to grow (but not negative PE)
    if e["pe"] and e["pe"] > 0 and e["pe"] < 100:
        score += max(0, (100 - e["pe"]) / 100 * 10)
    # ROE bonus: high ROE = quality company
    if e["roe"] and e["roe"] > 5:
        score += min(10, e["roe"] / 3)
    # Small/mid cap bonus for growth potential
    if e["market_cap"] and e["market_cap"] < 5e10:  # < 500亿
        score += 5
    elif e["market_cap"] and e["market_cap"] < 2e10:  # < 200亿
        score += 8
    return score

ranged_stocks = defaultdict(list)
for e in enriched:
    for label, lo, hi in PRICE_RANGES:
        if lo <= e["price"] < hi:
            e["growth_score"] = compute_growth_score(e)
            ranged_stocks[label].append(e)
            break

# Sort each range by growth score
for label in ranged_stocks:
    ranged_stocks[label].sort(key=lambda x: x["growth_score"], reverse=True)

# Print summary
print("\n" + "=" * 80)
print("📊 STOCK DISTRIBUTION BY PRICE RANGE")
print("=" * 80)
for label, lo, hi in PRICE_RANGES:
    stocks = ranged_stocks.get(label, [])
    top_n = min(30, len(stocks))
    print(f"  ¥{label:>12}: {len(stocks):>4} stocks → selecting top {top_n}")

# ── Step 6: DeepSeek AI Growth Analysis ────────────────────────────
api_key = os.environ.get("DEEPSEEK_API_KEY", config.ai.api_key)
if not api_key:
    print("\n⚠️  No DeepSeek API key. Skipping AI analysis.")
    print("   Set DEEPSEEK_API_KEY in .env to enable AI-powered growth assessment.")
else:
    client = DeepSeekClient(
        api_key=api_key,
        base_url=config.ai.base_url,
        model=config.ai.model,
        max_tokens=config.ai.max_tokens,
        temperature=config.ai.temperature,
        max_concurrent=3,
    )

    GROWTH_ANALYSIS_PROMPT = """你是一位资深A股成长股投资分析师。请对以下股票进行3年成长潜力分析。

股票: {stock_name} ({symbol})
当前价格: ¥{current_price}
行业: {industry}
当前市值: {market_cap}
市盈率(动态): {pe}
市净率: {pb}
净资产收益率: {roe}%
量化综合评分: {composite_score}/100
量化预测收益: {predicted_return}%
动量得分: {momentum}/100
风险等级: {risk_level}

请从以下维度分析该股票3年内涨幅达到2倍（200%）以上的可能性：

1. **行业赛道**: 所处行业是否有政策支持、技术变革或市场扩张红利？
2. **公司竞争力**: 在行业中是否具备独特竞争优势（技术、品牌、渠道、成本等）？
3. **成长驱动**: 未来3年的核心增长驱动因素是什么？（新产品、新市场、产能扩张、并购等）
4. **估值弹性**: 当前估值是否合理？业绩增长+估值提升能否支撑2倍以上涨幅？
5. **风险因素**: 最大的2-3个风险是什么？
6. **综合判断**: 3年内达到2倍涨幅的概率评估（高/中/低），并给出简要逻辑

请以JSON格式输出，包含字段:
- industry_analysis (行业赛道分析, 1-2句)
- competitive_advantage (公司竞争力, 1-2句)
- growth_drivers (成长驱动, 1-2句)
- valuation_view (估值弹性判断, 1-2句)
- risk_factors (风险因素, 数组, 2-3条)
- growth_probability (3年2倍概率: "高" / "中" / "低")
- probability_reason (概率判断理由, 1-2句)
- estimated_3y_return (3年预估涨幅%, 数值)
- investment_rating (投资评级: "强烈推荐" / "推荐" / "中性" / "谨慎")
"""

    async def analyze_growth(entry):
        stock_name = entry["name"]
        symbol = entry["symbol"]
        pe_str = f"{entry['pe']:.1f}" if entry["pe"] else "N/A"
        pb_str = f"{entry['pb']:.1f}" if entry["pb"] else "N/A"
        roe_str = f"{entry['roe']:.1f}" if entry["roe"] else "N/A"
        mkt_cap_str = f"{entry['market_cap']/1e8:.0f}亿" if entry["market_cap"] else "N/A"

        prompt = GROWTH_ANALYSIS_PROMPT.format(
            stock_name=stock_name,
            symbol=symbol,
            current_price=f"{entry['price']:.2f}",
            industry=entry["industry"],
            market_cap=mkt_cap_str,
            pe=pe_str,
            pb=pb_str,
            roe=roe_str,
            composite_score=f"{entry['composite']:.1f}",
            predicted_return=f"{entry['pred_ret']:.1f}",
            momentum=f"{entry['momentum']:.1f}",
            risk_level=entry["risk"],
        )

        messages = [
            {"role": "system", "content": "你是专业的A股成长股投资分析师，擅长发现具有十倍潜力的成长股。请基于行业逻辑和公司基本面给出有洞见的分析。以JSON格式回复。"},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await client.analyze_json(messages)
            if response:
                return json.loads(response.strip())
        except Exception as e:
            print(f"  ⚠️ AI analysis failed for {symbol}: {e}")
        return None

    # Select top candidates per range for AI analysis
    print("\n" + "=" * 80)
    print("🤖 DEEPSEEK AI GROWTH POTENTIAL ANALYSIS")
    print("=" * 80)

    # Analyze top 15 per range (or all if fewer)
    all_ai_tasks = []
    for label, lo, hi in PRICE_RANGES:
        stocks = ranged_stocks.get(label, [])
        candidates = stocks[:min(15, len(stocks))]
        for e in candidates:
            all_ai_tasks.append((label, e))

    print(f"   Analyzing {len(all_ai_tasks)} stocks across {len(PRICE_RANGES)} ranges...")
    print(f"   This will take ~{len(all_ai_tasks)//3 + 1} batches with concurrency=3\n")

    async def run_batched_analysis():
        results = {}
        sem = asyncio.Semaphore(3)

        async def analyze_with_limit(label, entry):
            async with sem:
                print(f"  🔍 {label}: {entry['name']}({entry['symbol']}) ¥{entry['price']:.2f} ...")
                result = await analyze_growth(entry)
                if result:
                    print(f"     ✓ 评级={result.get('investment_rating','?')} | 3年2倍概率={result.get('growth_probability','?')} | 预估涨幅={result.get('estimated_3y_return','?')}%")
                else:
                    print(f"     ✗ 分析失败")
                return (label, entry["symbol"]), result

        tasks = [analyze_with_limit(label, e) for label, e in all_ai_tasks]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in batch_results:
            if isinstance(r, Exception):
                print(f"  ⚠️ Batch error: {r}")
                continue
            if r:
                key, result = r
                results[key] = result

        return results

    ai_results = asyncio.run(run_batched_analysis())
    print(f"\n✅ AI analysis complete: {len(ai_results)} stocks analyzed")

    # Merge AI results back into entries
    for entry in enriched:
        key = (None, entry["symbol"])
        # Find matching result
        for (label, sym), result in ai_results.items():
            if sym == entry["symbol"]:
                entry["ai_growth"] = result
                break

# ── Step 7: Generate Investment Estimates ──────────────────────────
def generate_investment_estimate(entry, ai_result=None):
    """Generate investment amount, holding period, return estimate."""
    price = entry["price"]
    risk = entry.get("risk", "medium")

    # Holding period based on risk level
    holding_map = {"low": "3年以上(长期)", "medium": "2-3年(中长期)", "high": "1-2年(中短期)"}
    holding = holding_map.get(risk, "2-3年")

    # Investment amount suggestion based on price and risk
    if price < 10:
        if risk == "low":
            amount = "5-10万元"
        elif risk == "medium":
            amount = "3-5万元"
        else:
            amount = "1-3万元"
    elif price < 50:
        if risk == "low":
            amount = "10-20万元"
        elif risk == "medium":
            amount = "5-10万元"
        else:
            amount = "3-5万元"
    elif price < 100:
        if risk == "low":
            amount = "20-30万元"
        else:
            amount = "10-15万元"
    else:
        amount = "30-50万元"

    # Return estimate
    # Use AI estimated return if available, otherwise use quant predicted return
    if ai_result and "estimated_3y_return" in ai_result:
        est_return = float(ai_result["estimated_3y_return"])
        prob = ai_result.get("growth_probability", "中")
    else:
        # Conservative estimate based on quant scores
        base_return = max(20, entry["composite"] * 0.8)  # 20-80% range
        if risk == "low":
            base_return *= 1.5
        elif risk == "high":
            base_return *= 0.5
        est_return = base_return
        prob = "中" if entry["composite"] > 30 else "低"

    # Annualized return
    annual_return = ((1 + est_return / 100) ** (1/3) - 1) * 100

    return {
        "investment_amount": amount,
        "holding_period": holding,
        "estimated_3y_return_pct": round(est_return, 1),
        "annualized_return_pct": round(annual_return, 1),
        "growth_probability_ai": prob,
        "target_price_3y": round(price * (1 + est_return/100), 2),
    }

# ── Step 8: Generate Final Report ──────────────────────────────────
print("\n" + "=" * 90)
print("📈 A股三年翻倍潜力股票分析报告")
print(f"   分析日期: {date.today()} | 数据日期: {latest}")
print("=" * 90)

today_str = date.today().strftime("%Y-%m-%d")
output_lines = []
output_lines.append(f"# A股三年翻倍潜力股票分析报告")
output_lines.append(f"\n**分析日期**: {today_str} | **数据基准日**: {latest}")
output_lines.append(f"\n**分析范围**: {len(enriched)}只股票 | **分析工具**: StockRec量化策略 + DeepSeek AI成长分析")
output_lines.append(f"\n---")

total_analyzed = 0

for label, lo, hi in PRICE_RANGES:
    stocks = ranged_stocks.get(label, [])
    if not stocks:
        continue

    top_n = min(30, len(stocks))
    selected = stocks[:top_n]

    print(f"\n{'─' * 80}")
    print(f"📊 价格区间: ¥{label} ({len(stocks)}只股票, 选取前{top_n})")
    print(f"{'─' * 80}")

    output_lines.append(f"\n## 价格区间: ¥{label}")
    output_lines.append(f"\n> 共{len(stocks)}只股票符合条件, 选取成长潜力前{top_n}名")
    output_lines.append(f"\n| 排名 | 股票 | 代码 | 现价(¥) | 行业 | 综合得分 | PE | ROE | 3年目标价(¥) | 预估涨幅 | 年化收益 | 3年2倍概率 | 投资评级 | 建议投资额 | 持有期限 |")
    output_lines.append(f"|------|------|------|---------|------|----------|----|-----|-------------|----------|----------|------------|----------|------------|----------|")

    for i, e in enumerate(selected):
        ai = e.get("ai_growth", {})
        est = generate_investment_estimate(e, ai)

        pe_str = f"{e['pe']:.1f}" if e['pe'] else "-"
        roe_str = f"{e['roe']:.1f}%" if e['roe'] else "-"
        ind_str = e['industry'][:12] if e['industry'] else "-"

        prob = est["growth_probability_ai"]
        prob_icon = {"高": "🟢高", "中": "🟡中", "低": "🔴低"}.get(prob, prob)

        rating = ai.get("investment_rating", "-") if ai else "-"

        print(f"{i+1:2d}. {e['name']:<8s} ¥{e['price']:<8.2f} | 综合{e['composite']:.0f} | {pe_str} | {prob_icon} | 3年目标¥{est['target_price_3y']:.0f} | +{est['estimated_3y_return_pct']:.0f}% | {rating}")
        if ai and ai.get("growth_drivers"):
            print(f"    驱动: {ai['growth_drivers'][:80]}")
        if ai and ai.get("risk_factors"):
            risks = ai["risk_factors"] if isinstance(ai["risk_factors"], list) else [ai["risk_factors"]]
            print(f"    风险: {'; '.join(risks[:2])[:80]}")

        output_lines.append(
            f"| {i+1} | {e['name']} | {e['symbol']} | {e['price']:.2f} | {ind_str} | {e['composite']:.0f} | {pe_str} | {roe_str} | {est['target_price_3y']:.2f} | +{est['estimated_3y_return_pct']:.1f}% | {est['annualized_return_pct']:.1f}% | {prob_icon} | {rating} | {est['investment_amount']} | {est['holding_period']} |"
        )
        total_analyzed += 1

    # Per-range summary
    high_prob = sum(1 for e in selected if e.get("ai_growth", {}).get("growth_probability") == "高")
    mid_prob = sum(1 for e in selected if e.get("ai_growth", {}).get("growth_probability") == "中")
    output_lines.append(f"\n**区间小结**: 高概率{high_prob}只, 中等概率{mid_prob}只")

# ── Step 9: Overall Summary ────────────────────────────────────────
output_lines.append(f"\n---")
output_lines.append(f"\n## 投资策略建议")
output_lines.append(f"\n### 仓位分配建议")
output_lines.append(f"\n| 价格区间 | 建议仓位占比 | 风险等级 | 适合投资者类型 |")
output_lines.append(f"|----------|-------------|----------|----------------|")
output_lines.append(f"| <20元(低价成长) | 25% | 中高风险 | 激进型/成长型 |")
output_lines.append(f"| 20-50元(中小盘) | 25% | 中风险 | 成长型/均衡型 |")
output_lines.append(f"| 50-100元(中盘) | 20% | 中低风险 | 均衡型 |")
output_lines.append(f"| 100元以上(大盘) | 30% | 低风险 | 稳健型/均衡型 |")

output_lines.append(f"\n### 风险提示")
output_lines.append(f"\n1. **三年两倍属于高回报预期**, 年化收益约26%, 需要较高的成长性和市场配合")
output_lines.append(f"2. **低价股不等于便宜**, 部分低价股有基本面隐患, 需结合PE/ROE谨慎判断")
output_lines.append(f"3. **行业轮动风险**, A股风格切换频繁, 建议分散行业配置")
output_lines.append(f"4. **流动性风险**, 部分小市值股票流动性不足, 大资金进出困难")
output_lines.append(f"5. **本报告仅供参考**, 不构成投资建议, 投资有风险, 入市需谨慎")

output_lines.append(f"\n---")
output_lines.append(f"\n*报告由 StockRec 鲸灵宝选股系统自动生成*")
output_lines.append(f"\n*量化模型: 3层因子打分 + 机器学习预测 + 事件驱动*")
output_lines.append(f"\n*AI分析: DeepSeek 成长潜力评估*")

# Write report
report_path = f"data/reports/growth_analysis_{today_str}.md"
os.makedirs("data/reports", exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print(f"\n{'=' * 80}")
print(f"✅ 分析完成! 共筛选 {total_analyzed} 只股票")
print(f"📄 完整报告: {report_path}")
print(f"{'=' * 80}")

session.close()
