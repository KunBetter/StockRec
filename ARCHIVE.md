# StockRec（鲸灵宝）项目归档

> 归档日期：2026-06-28 | 最后提交：`f5424ed` (set)
> 项目定位：AI 深度选股推荐系统 —「AI深度选股 · 如鲸探宝」

---

## 一、项目摘要

StockRec 是一个面向 A 股投资者的 AI+量化双引擎选股推荐系统。通过三层量化策略（多因子 + LightGBM 机器学习 + 事件驱动）对全市场股票打分排序，再由 DeepSeek 大模型进行语义分析增强，最终输出可解释的选股推荐、AI 市场简报、多股对比和 3 年成长潜力评估。

前后端完整分离，支持 Web (React 19) 和移动端 (React Native 0.76)，后端基于 FastAPI，定时任务通过 APScheduler 全流程自动化（数据更新 → 策略打分 → AI 分析 → 模型重训）。

---

## 二、技术架构

```
┌──────────────────────────────────────────────────────┐
│                   前端层                               │
│  frontend/ (React 19 + TailwindCSS 4 + Vite 8)       │
│  mobile/   (React Native 0.76)                       │
├──────────────────────────────────────────────────────┤
│                  API 网关层                            │
│  FastAPI + CORS + WebSocket                          │
│  /api/v1/{auth,stocks,recommendations,market,        │
│           analysis,ai,profile,data}                  │
├──────────────────────────────────────────────────────┤
│                选股策略引擎 (三层)                     │
│  Layer1: 20+ 多因子 (60%) — 价值/质量/动量/成长等     │
│  Layer2: LightGBM 预测 (30%) — 252日特征 → 20日收益   │
│  Layer3: 事件驱动 (10%) — 财报惊喜/回购/高分红         │
│  → CompositeScore + RiskClassifier (低/中/高)         │
├──────────────────────────────────────────────────────┤
│                 AI 分析层                              │
│  DeepSeek-chat via OpenAI SDK                        │
│  - 财报解读 · 新闻情绪 · 行业趋势 · 综合推荐理由       │
│  - SSE 流式对话 · JSON 结构化分析                      │
├──────────────────────────────────────────────────────┤
│                 数据层 (四源冗余)                      │
│  Baostock (历史K线+财务) → AKShare (实时+资金流)      │
│  新浪API (实时快照) → 腾讯API (实时快照)              │
│  DataOrchestrator 容错 fallback 链                    │
│  Parquet 存储 K线 | SQLite/PG 存储结构化数据          │
│  Redis 缓存                                          │
├──────────────────────────────────────────────────────┤
│              调度自动化 (APScheduler)                  │
│  hourly_update | daily_close | strategy_scoring       │
│  model_retrain | ai_analysis | weekly_full_sync       │
└──────────────────────────────────────────────────────┘
```

---

## 三、目录结构

```
StockRec/
├── backend/                        # Python 后端
│   ├── main.py                     # FastAPI 入口 + lifespan
│   ├── config.py                   # Pydantic 配置模型 + YAML 加载
│   ├── ai/                         # AI 客户端
│   │   └── deepseek_client.py      # DeepSeek (OpenAI SDK)
│   ├── api/                        # API 层
│   │   ├── router.py               # 路由汇总
│   │   ├── schemas.py              # Pydantic schema
│   │   └── endpoints/
│   │       ├── recommendations.py  # 选股推荐 + 简报 + 同行
│   │       ├── analysis.py         # 深度分析
│   │       ├── ai.py               # AI 对话 (SSE 流式)
│   │       ├── stocks.py           # 股票 CRUD + 对比
│   │       ├── market.py           # 市场概览
│   │       ├── auth.py             # 登录认证
│   │       ├── profile.py          # 用户自选/历史
│   │       ├── data.py             # 数据新鲜度
│   │       └── websocket.py        # WebSocket
│   ├── strategy/                   # 选股策略引擎
│   │   ├── engine.py               # StrategyEngine 主入口
│   │   ├── layer1_factors/         # 多因子计算
│   │   │   ├── pipeline.py         # 因子管线
│   │   │   ├── registry.py         # 因子注册表
│   │   │   ├── base_factor.py      # 因子基类
│   │   │   ├── value_factors.py    # EP/BP/SP/股息率
│   │   │   ├── quality_factors.py  # ROE/ROA/毛利率
│   │   │   ├── momentum_factors.py # 1/3/12月动量
│   │   │   ├── growth_factors.py   # 营收/利润增速
│   │   │   ├── reversal_factors.py # 短周期反转
│   │   │   ├── volatility_factors.py # 波动率
│   │   │   ├── liquidity_factors.py  # 换手率/非流动性
│   │   │   └── capital_flow_factors.py # 主力/北向/融资
│   │   ├── layer2_ml/              # 机器学习
│   │   │   ├── model_predictor.py  # LightGBM 预测
│   │   │   ├── model_trainer.py    # 模型训练
│   │   │   └── feature_builder.py  # 特征工程
│   │   ├── layer3_events/          # 事件驱动
│   │   │   ├── event_scorer.py     # 事件打分
│   │   │   ├── earnings_surprise.py
│   │   │   ├── buyback_detector.py
│   │   │   └── high_dividend.py
│   │   └── utils/
│   │       ├── scorer.py           # CompositeScorer + RiskClassifier
│   │       ├── neutralizer.py      # 行业/市值中性化
│   │       └── filter.py           # ST/停牌/涨跌停过滤 + ETF/指数排除
│   ├── data/                       # 数据源客户端
│   │   ├── data_orchestrator.py    # 多源编排 + 符号规范化
│   │   ├── baostock_client.py      # 历史 K 线 + 财务
│   │   ├── akshare_client.py       # 实时行情 + 资金流
│   │   ├── sina_client.py          # 实时快照
│   │   ├── tencent_client.py       # 实时快照
│   │   └── normalizer.py           # 数据标准化
│   ├── persistence/                # 持久化
│   │   ├── database.py             # SQLAlchemy engine/session
│   │   ├── models.py               # 10 张 ORM 表
│   │   ├── repository.py           # 通用 Repository
│   │   ├── parquet_store.py        # Parquet K线存储
│   │   └── redis_client.py         # Redis 客户端
│   ├── scheduler/                  # 定时任务
│   │   ├── scheduler.py            # APScheduler 封装
│   │   └── jobs/
│   │       ├── hourly_update.py    # 每小时更新数据
│   │       ├── daily_close.py      # 收盘处理
│   │       ├── run_strategy.py     # 策略引擎打分
│   │       ├── ai_analysis_job.py  # AI 分析
│   │       ├── model_retrain.py    # 模型重训
│   │       └── weekly_full_sync.py # 全量同步
│   ├── auth/                       # 认证
│   │   ├── service.py              # JWT 签发/验证
│   │   ├── schemas.py
│   │   └── dependencies.py
│   └── tests/                      # 测试
│       ├── test_api_recommendations.py
│       ├── test_strategy_engine.py
│       └── test_parquet_store.py
│
├── frontend/                       # Web 前端
│   ├── src/
│   │   ├── App.tsx                  # 主应用 (TabBar + 页面路由)
│   │   ├── components/
│   │   │   ├── home/                # 首页组件
│   │   │   │   ├── StarPick.tsx     # 明星推荐卡片
│   │   │   │   ├── StockTable.tsx   # 列表视图 + 多选对比
│   │   │   │   ├── CompactStockCard.tsx
│   │   │   │   ├── AIBriefingCard.tsx
│   │   │   │   ├── QuickActions.tsx
│   │   │   │   └── ViewToggle.tsx   # 推荐流/列表视图切换
│   │   │   ├── filter/FilterPanel.tsx # 筛选面板
│   │   │   ├── analysis/           # 深度分析页
│   │   │   │   ├── StockAnalysis.tsx
│   │   │   │   ├── LayerBreakdown.tsx
│   │   │   │   ├── ContributionChart.tsx
│   │   │   │   ├── AIAnalysis.tsx
│   │   │   │   ├── PeerComparison.tsx
│   │   │   │   └── AnalysisModal.tsx
│   │   │   ├── compare/ComparePage.tsx # 多股对比
│   │   │   ├── chat/AIChatPage.tsx  # AI 对话 (SSE)
│   │   │   ├── layout/             # 布局
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── TabBar.tsx
│   │   │   │   └── StatusBar.tsx
│   │   │   ├── stocks/             # 通用股票组件
│   │   │   ├── common/             # Loading/Error/Empty 状态
│   │   │   ├── pages/              # 市场/个人中心页
│   │   │   └── sections/RiskSection.tsx
│   │   ├── hooks/useStocks.ts      # 数据获取 hook
│   │   ├── services/api.ts         # API 调用封装
│   │   └── types/stock.ts          # TypeScript 类型定义
│   ├── package.json                # React 19 + Vite 8 + Tailwind 4
│   └── vite.config.ts
│
├── mobile/                         # React Native 移动端
│   ├── App.tsx
│   ├── src/
│   │   ├── screens/                # 登录/推荐/市场/个股/个人
│   │   ├── components/             # StockCard/ScoreBar/RiskBadge
│   │   ├── hooks/                  # useStocks/useStockDetail/useWebSocket
│   │   ├── services/api.ts
│   │   └── store/AuthContext.tsx
│   └── package.json                # RN 0.76
│
├── scripts/                        # 独立脚本
│   ├── analyze_growth_potential.py # 3年2倍成长潜力分析 ★ 最新
│   ├── backfill_kline.py           # K线数据回填
│   ├── run_ai_analysis.py          # AI 分析批量运行
│   ├── seed_demo_data.py           # 演示数据填充
│   ├── compare_snapshots.py        # 快照对比
│   └── migrate_sqlite_to_pg.py     # SQLite → PG 迁移
│
├── data/                           # 数据文件 (gitignored)
│   ├── database/stockrec.db        # SQLite 主库
│   ├── parquet/kline/              # K线 Parquet 存档
│   ├── reports/                    # 分析报告输出
│   │   └── growth_analysis_2026-06-27.md
│   └── snapshots/                  # 推荐快照
│       └── recommendations_2x_potential_2026-06-27.{md,json}
│
├── alembic/                        # 数据库迁移
│   ├── env.py
│   └── versions/
│       ├── 533cfc099225_init_schema.py
│       ├── 06281f950a18_add_watchlist.py
│       └── 189a2adad7f3_add_stock_data_freshness.py
│
├── docs/                           # 项目文档
│   ├── 01-数据源调研.md
│   ├── 02-选股策略调研.md
│   ├── 03-AI与量化策略协同机制.md
│   ├── 04-商业化评估与变现路径.md
│   ├── 初期变现方案.md
│   ├── 部署发布指南.md
│   └── superpowers/               # AI 生成的开发计划
│       ├── plans/2026-05-30-ai-first-redesign.md
│       └── specs/2026-05-30-ai-first-redesign.md
│
├── config.yaml                     # 生产配置
├── config.example.yaml             # 配置模板
├── requirements.txt                # Python 依赖
├── requirements-dev.txt
├── CLAUDE.md                       # AI 助手指南
├── README.md
└── ARCHIVE.md                      # 本文件
```

---

## 四、数据模型 (10 张核心表)

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `users` | 用户账户 | phone, nickname, is_active |
| `stocks` | 股票基本面 | symbol, name, industry, pe_ttm, pb, roe, dividend_yield, market_cap, is_st, status |
| `daily_kline_metadata` | K 线索引 | symbol, trade_date, open/high/low/close/preclose, volume, amount, turn_rate, pct_change, parquet_file |
| `financial_data` | 财报数据 | symbol, report_date, revenue, net_profit, eps, total_assets, operating_cf, investing_cf, financing_cf |
| `factor_scores` | 因子得分 | symbol, calc_date, factor_name, raw_value, z_score, percentile |
| `recommendations` | 推荐结果 ★核心 | symbol, trade_date, layer1_factor_score, layer2_ml_score, layer3_event_score, composite_score, predicted_return, momentum_score, quality_score, sentiment_score, risk_level, risk_score, current_price, price_change_pct, holding_period, ai_summary, ai_full_analysis, ai_risk_flags, rank |
| `fund_flows` | 资金流向 | symbol, trade_date, main_net_inflow, super_large_inflow, northbound_holding, margin_balance |
| `news_sentiment` | 舆情分析 | symbol, news_date, title, sentiment_label, sentiment_score, ai_processed |
| `market_indices` | 市场指数 | index_code, trade_date, open/high/low/close, volume, pct_change |
| `watchlist` | 自选股 | user_id, symbol |
| `execution_logs` | 任务日志 | job_name, started_at, finished_at, status, records_processed, duration_ms |

---

## 五、API 端点清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 |
| POST | `/api/v1/auth/login` | 手机号登录 |
| POST | `/api/v1/auth/register` | 注册 |
| GET | `/api/v1/recommendations` | 选股推荐列表（支持 price/industry/risk/sort 过滤） |
| GET | `/api/v1/recommendations/briefing` | AI 大盘简报 |
| GET | `/api/v1/recommendations/{symbol}` | 单股推荐详情 |
| GET | `/api/v1/recommendations/{symbol}/peers` | 同行业对比 |
| GET | `/api/v1/analysis/{symbol}` | 深度分析（含 AI 分析 JSON） |
| POST | `/api/v1/stocks/compare` | 多股对比 + AI 评判 |
| POST | `/api/v1/ai/chat` | DeepSeek SSE 流式对话 |
| GET | `/api/v1/market/overview` | 市场概览（指数/板块涨跌/异动） |
| GET | `/api/v1/profile/watchlist` | 我的自选股 |
| POST | `/api/v1/profile/watchlist/{symbol}` | 添加自选 |
| DELETE | `/api/v1/profile/watchlist/{symbol}` | 移除自选 |
| GET | `/api/v1/profile/history` | 推荐历史 |
| GET | `/api/v1/profile/status` | 系统状态 |
| GET | `/api/v1/data/freshness` | 数据新鲜度检查 |

---

## 六、策略引擎详解

### 6.1 Layer1: 多因子 (权重 60%)

八类因子池，截面 z-score 标准化 + 去极值 (Winsorize 3σ) + ICIR 加权：

| 因子类别 | 因子 | 方向 |
|---------|------|:---:|
| 价值 | EP(1/PE), BP(1/PB), SP, 股息率 | + |
| 质量 | ROE, ROA, 毛利率, 资产周转率 | + |
| 动量 | 20日动量, 60日动量, 12-1月动量 | + |
| 成长 | 营收增速, 利润增速 | + |
| 反转 | 5日反转, 日内反转 | - |
| 波动 | 历史波动率, 下行波动率 | - |
| 流动性 | 换手率, Amihud 非流动性, 换手率变动 | -/+ |
| 资金 | 主力净流入, 北向资金占比, 融资余额变化 | + |

### 6.2 Layer2: ML 预测 (权重 30%)

LightGBM 监督学习：252 日量价时序特征 + 财务特征 + 资金流特征 → 预测未来 20 日收益率。时间序列交叉验证，日频滚动重训练。

### 6.3 Layer3: 事件驱动 (权重 10%)

| 事件 | 权重 | 触发条件 |
|------|:---:|---------|
| 业绩超预期 | 60% | 净利润同比增速 > 20% |
| 高股息预案 | 30% | 股息率 > 4% |
| 股票回购 | 10% | 公司发布回购公告 |

### 6.4 综合评分

```
composite_score = predicted_return × 0.5
                + momentum_score  × 0.2
                + quality_score   × 0.2
                + sentiment_score × 0.1

风险分级：低 ≤30 / 中 30-60 / 高 ≥60
目标输出：Top 30 (max_per_industry_pct ≤ 25%)
```

---

## 七、调度任务详情

| 任务 | 触发时间 | 功能 |
|------|---------|------|
| hourly_update | 工作日 9:00-15:00 整点 | 获取实时股价 + 因子更新 |
| daily_close | 工作日 15:30 | 收盘后数据处理 |
| strategy_scoring | 工作日 16:15 | 运行 StrategyEngine.run() 全量打分 |
| model_retrain | 工作日 16:30 | 用最新数据重训 LightGBM 模型 |
| ai_analysis | 工作日 9:45-15:45 整点 | DeepSeek 对 Top 30 增量分析 |
| weekly_full_sync | 周日 8:00 | 全市场股票基本信息 + K线全量同步 |

脚本 `scripts/analyze_growth_potential.py` 独立运行，执行"3 年翻倍潜力"全量分析。

---

## 八、部署配置

### 8.1 环境需求

- Python 3.10+ + requirements.txt
- Node.js 20+ (前端 Vite 8)
- SQLite (开发) / PostgreSQL 15 (生产)
- Redis 7.0
- 阿里云 ECS + RDS + Redis + OSS (生产)
- DeepSeek API Key

### 8.2 核心配置项 (config.yaml)

```yaml
strategy:
  stock_universe: "csi300_csi500"  # 选股范围
  layer_weights: {layer1_factor: 0.6, layer2_ml: 0.3, layer3_event: 0.1}
  composite_score_weights: {predicted_return: 0.5, momentum_score: 0.2, quality_score: 0.2, sentiment_score: 0.1}
  output: {top_n: 30, max_per_industry_pct: 0.25}
ai:
  provider: "deepseek"
  model: "deepseek-chat"
  max_tokens: 2000
  temperature: 0.3
```

### 8.3 启动命令

```bash
# 后端
cd backend && uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端 (开发)
cd frontend && npm run dev    # → http://localhost:5173

# 独立脚本
python scripts/analyze_growth_potential.py
```

---

## 九、待完成事项

| 优先级 | 事项 | 说明 |
|:---:|------|------|
| 高 | API 鉴权加固 | auth 模块存在但核心接口未强制鉴权 |
| 高 | 移动端完善 | React Native 骨架存在，UI/交互待补全 |
| 中 | PostgreSQL 迁移 | 当前默认 SQLite，生产需切换到 PG |
| 中 | 模型版本管理 | LightGBM 模型缺少版本追踪和 A/B 测试 |
| 中 | Docker 化部署 | compose 目录和文件待创建 |
| 中 | CI/CD | GitHub Actions 流水线待配置 |
| 低 | AI fallback 策略 | DeepSeek 不可用时的降级方案 |
| 低 | 单元测试覆盖 | 仅 3 个测试文件，覆盖率低 |

---

## 十、Git 提交历史摘要

```
f5424ed set
152c678 feat: add growth potential analysis script and index/ETF filter
1650aba c
94d8eed fix: fill missing stock data — PE/ROE/dividend, industry, market index, AI summaries
19fbb75 fix: strategy engine never runs, causing stale recommendations
fa1ec22 feat: FilterPanel with presets and risk filtering
804a0a8 feat: stock compare endpoint with AI verdict
7f300b8 feat: ComparePage with multi-stock comparison and AI verdict
d4dfc6b feat: SSE chat endpoint integrated with DeepSeek
d0233ac feat: AIChatPage with SSE streaming from DeepSeek
a426d58 feat: add peers endpoint and peer_rank to analysis
...
09f09c1 feat: ViewToggle component for featured/list switch
```

---

## 十一、技术债务记录

1. **会话管理**：`get_session()` 直接调用，无依赖注入，测试困难
2. **单机架构**：SQLite + 本地 Parquet，横向扩展受限
3. **引擎循环中 O(n) DB 查询**：`engine.py:74-76` 在循环内做 `next()` 查找，随着股票池扩大性能会劣化
4. **事件层打分是空实现**：`event_scorer.score()` 看似只返回默认值，未实际接入事件数据
5. **前端的 `PriceRangeSelector` 组件存在但未在 FilterPanel 中使用**
6. **移动端缺少完整的 API service 对接**

---

## 十二、文件统计数据

| 类别 | 数量 |
|------|:---:|
| Python 后端文件 | 50+ |
| TypeScript/TSX 前端文件 | 54 |
| 数据库迁移 | 3 |
| 项目文档 | 7+ |
| K线 Parquet 存档 (股票数×年份) | 多文件 |
| requirements 依赖 | 20+ |

---

---

## 十三、改进计划

### 计划概述

基于代码审查，将改进分为四个 Phase，按 ROI (投入产出比) 排序。每个 Phase 产出可独立交付。

---

### Phase 1：策略引擎精度提升（预计 2-3 周）

当前引擎可运行，但存在多个影响选股质量的问题。

#### 1.1 修复 Layer3 事件层空跑

**现状**：`engine.py:116` 调用 `self.event_scorer.score()` 不传任何参数，事件检测器从未接入实际数据。

```python
# engine.py:116 — 当前
event_score = self.event_scorer.score()  # 永远返回 0

# 应改为
fin_data = fin_repo.find_one_by(symbol=symbol, report_date=...)  # 取最近财报
event_score = self.event_scorer.score(
    financial_data=fin_data,
    dividend_yield=stock.dividend_yield,
    has_buyback=...  # 从 news_sentiment 或公告数据获取
)
```

**影响**：Layer3 占 10% 权重，实际贡献为零。修复后可捕捉业绩超预期、高分红、回购等强信号。

**依赖**：需确认 `financial_data` 表中有足够数据 (财报季数据)；若无，先在 `hourly_update` 中补齐。

#### 1.2 引擎 O(n²) 循环优化

**现状**：`engine.py:74-76` 在 `for symbol in symbol_list` 循环内做 O(n) 的 `next()` 查找。

```python
# 当前 — 每次内循环 O(n)
stock = next((s for s in stocks if hasattr(s, 'symbol') ...), None)

# 改进 — 循环前建 lookup dict
stock_by_symbol = {getattr(s, 'symbol', None): s for s in stocks}
```

**影响**：800 只股票时，每个循环多出 800 次属性访问。改为 dict lookup 后 O(1)。

#### 1.3 因子数据传入修复

**现状**：`engine.py:80` `factor_pipeline.compute_all_factors(df)` 只传 K线，财务数据和资金流从未传入因子计算。

```python
# 当前
factor_values = self.factor_pipeline.compute_all_factors(df)

# 改进
fin = fin_by_symbol.get(symbol, {})
flow = flow_by_symbol.get(symbol, {})
factor_values = self.factor_pipeline.compute_all_factors(df, financials=fin, fund_flows=flow)
```

**影响**：价值因子 (PE/PB)、质量因子 (ROE)、资金流向因子从未参与计算，Layer1 仅基于量价数据打分。

#### 1.4 ML 模型冷启动

**现状**：`model_predictor.py` 加载 `data/models/lgb_model_latest.pkl`，若文件不存在返回 None，predict() 返回默认值。

**方案**：
- 脚本 `scripts/backfill_kline.py` 已有数据回填能力，增加 `--train-model` 参数
- 回填完成后自动训练初始 LightGBM 模型并写入 `data/models/`
- 后续由 `model_retrain` 定时任务每日更新

#### 1.5 策略回测框架

**现状**：无回测能力，策略参数调整全靠经验。

**新增**：`backend/strategy/backtest.py`
```python
class BacktestEngine:
    def run(self, start_date, end_date, config) -> BacktestResult:
        # 按日滚动运行 StrategyEngine，追踪每日 Top N 后续收益
        # 输出：年化收益、夏普比率、最大回撤、IC 序列
```

**优先级**：中。回测框架是后续所有参数调优的基础。

---

### Phase 2：数据层健壮性（预计 1-2 周）

#### 2.1 财务数据自动补齐

**现状**：`financial_data` 表可能为空或覆盖不全，导致质量因子和事件层无法工作。

**方案**：
- 在 `weekly_full_sync` 中增加：遍历所有 active 股票，从 Baostock 拉取最近 4 个季度的财报数据
- AkShare 作为 fallback 源

#### 2.2 数据新鲜度告警

**现状**：`/data/freshness` endpoint 只返回状态，不主动告警。

**方案**：
- 在 `hourly_update` 末尾检查：若最近更新时间 > 2 小时，写 ERROR 日志
- 增加 `/data/freshness` 返回各数据源最后成功时间
- 可选的 Telegram/钉钉 webhook 告警

#### 2.3 Parquet 数据分区优化

**现状**：按年份分区 (`2025.parquet`, `2026.parquet`)，跨年查询需合并多个文件。

**改进**：`read_kline()` 增加日期范围参数，自动拼接所需年份文件。当前每次读全部年份数据。

---

### Phase 3：生产就绪（预计 2-3 周）

#### 3.1 API 鉴权强制

**现状**：auth 模块存在但核心接口 (recommendations, analysis) 无鉴权保护。

**方案**：
```python
# 在 router.py 或各 endpoint 加 dependency
from backend.auth.dependencies import get_current_user
router = APIRouter(dependencies=[Depends(get_current_user)])
```

**注意**：需要 JWT token 传递方式决策 — Bearer header (标准) 或 cookie (SPA 更简单)。

#### 3.2 会话管理重构

**现状**：`get_session()` 散落在 30+ 处，无连接池管理，测试困难。

**方案**：引入 FastAPI `Depends` 依赖注入：
```python
def get_db():
    session = get_session()
    try:
        yield session
    finally:
        session.close()

@router.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db)):
    ...
```

所有 endpoint 逐一迁移。这是大改动但收益高：统一生命周期、易于 mock 测试。

#### 3.3 数据库连接池

**现状**：每次调用 `get_session()` 创建新 engine。生产环境下应复用连接池。

**方案**：`database.py` 的 `get_engine()` 改为单例，全局共享一个 engine 实例。

#### 3.4 错误处理统一

**现状**：各 endpoint 的异常处理不一致，部分 try/except 吞掉异常。

**方案**：FastAPI exception handler 全局注册：
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
```

#### 3.5 Docker Compose 化

**现状**：`docs/部署发布指南.md` 引用了 `docker/docker-compose.yml` 但该文件不存在。

**创建**：`docker/docker-compose.yml` + `docker/Dockerfile` + `docker/nginx.conf`
```
services:
  app:      # FastAPI + uvicorn
  frontend: # nginx serving Vite build
  postgres: # PostgreSQL 15
  redis:    # Redis 7
```

---

### Phase 4：产品体验增强（预计 2-4 周）

#### 4.1 移动端功能补全

**现状**：React Native 项目有骨架 (screen 占位 + 基础组件)，但缺少完整的交互。

**待补**：
- RecommendationsScreen 对接真实 API
- StockDetailScreen 展示完整分析 + 图表
- AI 对话页接入 SSE
- 自选股管理 (添加/删除/排序)
- Push 通知 (接入极光/个推)

#### 4.2 前端性能优化

**现状**：`App.tsx` 一次性加载所有组件 (React.lazy 已用但可进一步优化)。

**改进**：
- `CompactStockCard` 虚拟列表 (长列表场景)
- API 响应缓存 (SWR/React Query 替代手写 useStocks hook)
- 图片懒加载 (如果有股票 Logo)
- Bundle 分析 + tree-shaking

#### 4.3 前端 FilterPanel 增强

**现状**：FilterPanel 有预设但缺少 `PriceRangeSelector` 组件 (组件文件存在但未使用)。

**改进**：在 FilterPanel 中接入 PriceRangeSelector，与后端 API 的 `price_min/price_max` 参数联动。

#### 4.4 成长潜力分析脚本产品化

**现状**：`scripts/analyze_growth_potential.py` 是独立脚本，需手动运行。

**方案**：
- 增加 API endpoint `POST /api/v1/analysis/growth-potential`，支持参数化价格区间
- 输出结果缓存到 Redis (避免重复调用 DeepSeek)
- 前端增加"成长潜力"页面，展示按价格区间分组的股票

#### 4.5 AI 对话上下文增强

**现状**：`POST /ai/chat` 仅注入 Top 10 股票摘要。

**改进**：增加以下上下文：
- 用户自选股列表
- 最近浏览的股票
- 当前市场情绪指标
- 支持多轮对话 (存储 session 历史)

---

### 改进优先级矩阵

| 改进项 | Phase | 工作量 | 影响面 | 风险 |
|--------|:---:|:---:|:---:|:---:|
| Layer3 事件层修复 | 1 | 小 | 中 | 低 |
| O(n²) 循环优化 | 1 | 小 | 低 | 低 |
| 因子数据传入修复 | 1 | 中 | 高 | 中 — 需验证财务数据完整性 |
| ML 冷启动 | 1 | 中 | 高 | 中 |
| 策略回测框架 | 1 | 大 | 高 | 低 |
| 财务数据补齐 | 2 | 中 | 高 | 中 |
| 数据新鲜度告警 | 2 | 小 | 低 | 低 |
| Parquet 分区优化 | 2 | 小 | 中 | 低 |
| API 鉴权强制 | 3 | 中 | 高 | 高 — 破坏性变更 |
| 会话管理重构 | 3 | 大 | 高 | 高 — 30+ 文件改动 |
| 连接池 | 3 | 小 | 中 | 低 |
| 错误处理统一 | 3 | 中 | 中 | 低 |
| Docker Compose | 3 | 大 | 高 | 低 |
| 移动端补全 | 4 | 大 | 中 | 低 |
| 前端性能 | 4 | 中 | 低 | 低 |
| 成长分析产品化 | 4 | 中 | 中 | 低 |
| AI 对话增强 | 4 | 中 | 低 | 低 |

---

### 建议执行路线

```
第 1-2 周：Phase 1.1-1.4 (策略引擎核心修复)
  → 产出：Layer3 实际工作、因子数据完整、ML 模型可用

第 3 周：Phase 1.5 (回测框架)
  → 产出：可验证策略有效性的工具

第 4 周：Phase 2 (数据层健壮)
  → 产出：数据可靠、有告警

第 5-6 周：Phase 3.1-3.4 (生产加固)
  → 产出：有鉴权、有连接池、有统一错误处理

第 7 周：Phase 3.5 (Docker 化部署)
  → 产出：一键部署

第 8-11 周：Phase 4 (产品体验)
  → 产出：移动端可用、前端流畅、功能完整
```

---

*本归档文件由代码分析自动生成，覆盖项目截至 2026-06-28 的完整状态。*
