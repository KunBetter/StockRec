#!/usr/bin/env python3
"""Seed the database with demo stock data and sample recommendations."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, datetime, timedelta
from backend.config import load_config
from backend.persistence.database import init_db, get_session
from backend.persistence.models import Stock, Recommendation, MarketIndex

config = load_config()
init_db(config.persistence.database.path)
session = get_session()

# Demo stocks
demo_stocks = [
    # symbol, code, name, exchange, industry, market_cap, target_price
    ("sh600036", "600036", "招商银行", "sh", "银行", 1080e8, 42.50),
    ("sh600519", "600519", "贵州茅台", "sh", "白酒", 2200e8, 1680.00),
    ("sz000858", "000858", "五粮液", "sz", "白酒", 780e8, 145.00),
    ("sh601318", "601318", "中国平安", "sh", "保险", 950e8, 52.00),
    ("sz300750", "300750", "宁德时代", "sz", "新能源", 1050e8, 185.00),
    ("sh600276", "600276", "恒瑞医药", "sh", "医药", 320e8, 48.50),
    ("sz002415", "002415", "海康威视", "sz", "安防", 380e8, 35.80),
    ("sh600900", "600900", "长江电力", "sh", "电力", 560e8, 22.30),
    ("sz000333", "000333", "美的集团", "sz", "家电", 480e8, 58.20),
    ("sh601012", "601012", "隆基绿能", "sh", "光伏", 210e8, 18.60),
    ("sz300059", "300059", "东方财富", "sz", "券商", 280e8, 8.45),
    ("sh688981", "688981", "中芯国际", "sh", "半导体", 350e8, 55.80),
    ("sz002594", "002594", "比亚迪", "sz", "汽车", 720e8, 255.00),
    ("sh600809", "600809", "山西汾酒", "sh", "白酒", 290e8, 210.00),
    ("sz000651", "000651", "格力电器", "sz", "家电", 230e8, 32.10),
    ("sh601899", "601899", "紫金矿业", "sh", "矿业", 420e8, 6.85),
    ("sz002142", "002142", "宁波银行", "sz", "银行", 240e8, 28.90),
    ("sh600030", "600030", "中信证券", "sh", "券商", 360e8, 25.40),
    ("sz000725", "000725", "京东方A", "sz", "面板", 180e8, 4.20),
    ("sh600887", "600887", "伊利股份", "sh", "食品", 200e8, 26.80),
    ("sz002230", "002230", "科大讯飞", "sz", "AI", 150e8, 52.30),
    ("sh688111", "688111", "金山办公", "sh", "软件", 200e8, 310.00),
    ("sz300124", "300124", "汇川技术", "sz", "工控", 180e8, 68.50),
    ("sh601857", "601857", "中国石油", "sh", "石油", 1500e8, 8.20),
    ("sz000002", "000002", "万科A", "sz", "地产", 120e8, 7.50),
]

today = date.today()

# Insert stocks
for item in demo_stocks:
    sym, code, name, ex, industry, mcap, _ = item
    existing = session.query(Stock).filter(Stock.symbol == sym).first()
    if not existing:
        s = Stock(
            symbol=sym, code=code, name=name, exchange=ex,
            industry=industry, market_cap=int(mcap), status="active",
        )
        session.add(s)
session.commit()
print(f"Inserted {len(demo_stocks)} stocks")

# Insert sample recommendations
import random
random.seed(42)

ai_summaries = {
    "low": [
        "Q1净利润同比增长12%，资产质量持续改善，不良率降至0.85%，拨备覆盖率提升至450%。高股息率提供安全边际。",
        "营收稳健增长8%，经营现金流充沛，估值处于历史低位，适合长期持有。",
        "核心业务护城河深厚，分红率达4.5%，ROE稳定在15%以上，防御属性突出。",
        "市场份额持续扩大，成本控制得力，盈利能力稳步提升，估值合理。",
        "行业龙头地位稳固，现金流充裕，连续10年提高分红，是典型的现金牛企业。",
    ],
    "medium": [
        "新产品线放量在即，研发投入占比15%，Q2业绩有望超预期。估值合理，成长性良好。",
        "受益于行业景气度回升，订单饱满，产能利用率提升至85%，未来两个季度营收增速有望加速。",
        "数字化转型初见成效，降本增效明显，市场对新业务线估值认可度提升。",
        "供需格局改善，产品价格企稳回升，库存去化接近尾声，业绩拐点或已出现。",
        "管理层增持彰显信心，公司回购计划进行中，基本面向好趋势明确。",
    ],
    "high": [
        "行业景气度触底反弹，公司作为弹性最大的标的，有望在行业反转中获得超额收益。短期波动较大。",
        "新技术路线突破带来想象空间，但商业化落地仍需时间验证。高风险高弹性标的。",
        "困境反转型机会，剥离亏损业务后轻装上阵，新管理层执行力强，但复苏节奏存在不确定性。",
        "主题投资热点，政策催化预期强烈，但基本面支撑较弱，适合短线波段操作。",
        "处于行业风口，市场关注度高，但估值已不便宜，需要业绩持续超预期支撑。",
    ],
}

recs = []

# Intentionally assign risk tiers with appropriate return profiles
# Low risk: stable earners, modest but reliable returns
# Medium risk: growth stocks, solid upside
# High risk: high-beta, big potential returns
risk_tiers = (
    ["low"] * 7 + ["medium"] * 13 + ["high"] * 5
)
random.shuffle(risk_tiers)

for idx, item in enumerate(demo_stocks):
    sym, code, name, ex, industry, mcap, base_price = item
    risk = risk_tiers[idx]

    # Generate scores that align with risk tier
    if risk == "low":
        composite = random.uniform(72, 95)
        pred_ret = round(random.uniform(3.0, 10.0), 1)
        momentum = round(random.uniform(65, 92), 1)
        quality = round(random.uniform(75, 95), 1)
    elif risk == "medium":
        composite = random.uniform(60, 85)
        pred_ret = round(random.uniform(8.0, 18.0), 1)
        momentum = round(random.uniform(55, 85), 1)
        quality = round(random.uniform(55, 82), 1)
    else:  # high
        composite = random.uniform(55, 72)
        pred_ret = round(random.uniform(15.0, 28.0), 1)
        momentum = round(random.uniform(60, 95), 1)
        quality = round(random.uniform(40, 70), 1)

    # Determine holding period based on risk, momentum and quality
    if risk == "high" and momentum > 70:
        holding = "1-2周"
    elif risk == "high":
        holding = "2-4周"
    elif risk == "medium" and momentum > 70:
        holding = "1-2个月"
    elif risk == "medium":
        holding = "2-3个月"
    elif quality > 85:
        holding = "6-12个月"
    else:
        holding = "3-6个月"
    sentiment = round(random.uniform(45, 85), 1)
    price = round(base_price * random.uniform(0.95, 1.05), 2)
    pct_change = round(random.uniform(-3, 5), 2)
    ai_summary = random.choice(ai_summaries[risk])

    existing = session.query(Recommendation).filter(
        Recommendation.symbol == sym, Recommendation.trade_date == today
    ).first()
    if not existing:
        r = Recommendation(
            symbol=sym,
            trade_date=today,
            layer1_factor_score=round(composite + random.uniform(-5, 5), 1),
            layer2_ml_score=round(composite + random.uniform(-8, 8), 1),
            layer3_event_score=round(random.uniform(0, 90), 1),
            predicted_return=pred_ret,
            momentum_score=momentum,
            quality_score=quality,
            sentiment_score=sentiment,
            composite_score=round(composite, 1),
            risk_level=risk,
            risk_score=round(100 - composite + random.uniform(-10, 10), 1),
            current_price=price,
            price_change_pct=pct_change,
            market_cap=int(mcap),
            holding_period=holding,
            ai_summary=ai_summary,
            rank=0,
        )
        session.add(r)
        recs.append(r)

session.commit()

# Assign ranks by composite score
sorted_recs = sorted(recs, key=lambda x: x.composite_score, reverse=True)
for i, r in enumerate(sorted_recs):
    r.rank = i + 1
session.commit()

print(f"Inserted {len(recs)} recommendations")
print(f"\nTop 5 by composite score:")
for r in sorted_recs[:5]:
    s = session.query(Stock).filter(Stock.symbol == r.symbol).first()
    print(f"  #{r.rank} {s.name}({r.symbol}) - {r.composite_score:.1f} [{r.risk_level}]")

# Seed market index demo data
index_data = [
    ("sh000001", "上证指数", 3350.12, 0.35),
    ("sz399001", "深证成指", 10820.45, 0.62),
    ("sz399006", "创业板指", 2215.33, 1.25),
    ("sh000688", "科创50", 985.60, 0.88),
]
for code, name, close_price, change in index_data:
    existing = session.query(MarketIndex).filter(
        MarketIndex.index_code == code, MarketIndex.trade_date == today
    ).first()
    if not existing:
        mi = MarketIndex(
            index_code=code, index_name=name, trade_date=today,
            open=close_price * 0.998, high=close_price * 1.012,
            low=close_price * 0.985, close=close_price,
            volume=random.randint(100000000, 500000000),
            amount=close_price * random.randint(1000000, 5000000),
            pct_change=change,
        )
        session.add(mi)
session.commit()
print(f"Inserted {len(index_data)} market indices")

session.close()
print("\nDone! Refresh http://localhost:5173")
