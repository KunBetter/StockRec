# 鲸灵宝 AI-First 改版 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 StockRec 从静态 demo 工具升级为 AI-First 实时选股系统，支持精选/列表双视图、三层引擎透明度、AI 问答和多股对比。

**Architecture:** 四阶段递进实施 — 先打好数据基础(D)，再改造前端布局(A)，然后深化 AI 透明度(B)，最后增加交互功能(C)。每阶段可独立验证。

**Tech Stack:** Python 3.14 + FastAPI + SQLAlchemy + Redis · React 18 + TypeScript + Vite + Tailwind CSS 4 + Framer Motion

---

## 文件结构

```
backend/
├── api/endpoints/
│   ├── recommendations.py  # [修改] 排序/筛选参数, briefing端点, peers端点
│   ├── ai.py               # [新增] SSE chat 端点
│   ├── data.py             # [新增] 数据时效性端点
│   └── stocks.py           # [修改] compare 端点
├── api/schemas.py          # [修改] 新增 schema
├── api/router.py           # [修改] 注册新路由
├── ai/deepseek_client.py   # [修改] chat_stream 方法
├── ai/prompts.py           # [修改] 新 prompt
├── scheduler/jobs/hourly_update.py  # [修改] 更新 Stock 表
├── persistence/models.py   # [修改] Stock 新增字段

frontend/src/
├── types/stock.ts          # [修改] 新类型
├── services/api.ts         # [修改] 新 API 函数
├── App.tsx                 # [重写] 路由化架构
├── components/layout/Header.tsx  # [修改] 动态状态栏
├── components/home/        # [新增目录]
│   ├── AIBriefingCard.tsx
│   ├── ViewToggle.tsx
│   ├── CompactStockCard.tsx
│   ├── StarPick.tsx
│   ├── StockTable.tsx
│   └── QuickActions.tsx
├── components/analysis/    # [新增目录]
│   ├── StockAnalysis.tsx
│   ├── LayerBreakdown.tsx
│   ├── ContributionChart.tsx
│   ├── AIAnalysis.tsx
│   └── PeerComparison.tsx
├── components/compare/
│   └── ComparePage.tsx     # [新增]
├── components/chat/
│   └── AIChatPage.tsx      # [新增]
└── components/filter/
    └── FilterPanel.tsx     # [新增]
```

---

## Phase D: 数据准确度

### Task D1: Stock 模型新增数据时效字段

**Files:**
- Modify: `backend/persistence/models.py:40-57`

- [ ] **Step 1: 添加字段**

在 `Stock` 类中 `is_suspended` 后添加两行:

```python
last_price_update = Column(DateTime)
data_source = Column(String(20))
```

- [ ] **Step 2: 创建 Alembic 迁移**

```bash
cd /Users/kunbetter/git/StockRec && .venv/bin/alembic revision --autogenerate -m "add_stock_data_freshness"
```

- [ ] **Step 3: 执行迁移**

```bash
.venv/bin/alembic upgrade head
```

Expected: `alembic_version` 表版本号递增，`stocks` 表新增两列。

- [ ] **Step 4: 验证**

```bash
python3 -c "
import sqlite3; conn = sqlite3.connect('data/database/stockrec.db')
cols = [c[1] for c in conn.execute('PRAGMA table_info(stocks)')]
print('last_price_update' in cols, 'data_source' in cols)
conn.close()
"
```

Expected: `True True`

- [ ] **Step 5: Commit**

```bash
git add backend/persistence/models.py data/database/stockrec.db
git add $(ls -t alembic/versions/*.py | head -1)
git commit -m "feat: add last_price_update and data_source to Stock model"
```

---

### Task D2: hourly_update 同步更新 Stock 表

**Files:**
- Modify: `backend/scheduler/jobs/hourly_update.py`

- [ ] **Step 1: 添加 Redis 缓存价格数据**

在文件顶部 import 后添加 Redis 缓存调用。将 `run_hourly_update` 的核心逻辑替换为:

```python
import logging
import json
from datetime import date, datetime

from backend.config import AppConfig
from backend.data.data_orchestrator import DataOrchestrator
from backend.persistence.database import get_session
from backend.persistence.models import Stock, Recommendation
from backend.persistence.redis_client import cache_set_json, cache_get_json

logger = logging.getLogger(__name__)

REALTIME_CACHE_KEY = "realtime:prices"
REALTIME_CACHE_TTL = 60

def run_hourly_update(config: AppConfig) -> int:
    session = get_session()
    try:
        stocks = session.query(Stock).filter(Stock.status == "active").all()
        if not stocks:
            logger.warning("No active stocks in database")
            return 0

        symbols = [s.symbol for s in stocks]
        orch = DataOrchestrator(config)
        df = orch.fetch_realtime_prices(symbols)
        orch.cleanup()

        if df.empty:
            logger.warning("No realtime data fetched")
            return 0

        today = date.today()
        now = datetime.utcnow()
        updated = 0

        price_data = {}
        for _, row in df.iterrows():
            symbol = row.get("symbol")
            if not symbol:
                continue
            price = row.get("price")
            pct = row.get("pct_change")
            if price is None:
                continue

            price_data[symbol] = {"price": float(price), "pct_change": float(pct) if pct is not None else 0, "updated": now.isoformat()}

            stock = session.query(Stock).filter(Stock.symbol == symbol).first()
            if stock:
                stock.last_price_update = now
                stock.data_source = "akshare"

            existing = session.query(Recommendation).filter(
                Recommendation.symbol == symbol, Recommendation.trade_date == today
            ).first()
            if existing:
                existing.current_price = float(price)
                if pct is not None:
                    existing.price_change_pct = float(pct)
            updated += 1

        session.commit()

        # Cache to Redis (fire and forget — ok if Redis is down)
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(cache_set_json(REALTIME_CACHE_KEY, price_data, REALTIME_CACHE_TTL))
            else:
                loop.run_until_complete(cache_set_json(REALTIME_CACHE_KEY, price_data, REALTIME_CACHE_TTL))
        except Exception:
            pass

        logger.info(f"Hourly update: {updated} prices updated")
        return len(df)
    finally:
        session.close()
```

- [ ] **Step 2: 验证语法**

```bash
.venv/bin/python3 -c "import ast; ast.parse(open('backend/scheduler/jobs/hourly_update.py').read()); print('OK')"
```

- [ ] **Step 3: Commit**

```bash
git add backend/scheduler/jobs/hourly_update.py
git commit -m "feat: update Stock table + Redis cache in hourly update job"
```

---

### Task D3: 数据时效性 API 端点

**Files:**
- Create: `backend/api/endpoints/data.py`
- Modify: `backend/api/router.py`

- [ ] **Step 1: 创建 data.py**

```python
from datetime import date, datetime

from fastapi import APIRouter, Request

from backend.persistence.database import get_session
from backend.persistence.models import Stock
from backend.persistence.redis_client import cache_get_json

router = APIRouter()

REALTIME_CACHE_KEY = "realtime:prices"


@router.get("/data/freshness")
def get_data_freshness(request: Request):
    config = request.app.state.config
    session = get_session()
    try:
        stocks = session.query(Stock).filter(Stock.status == "active").all()

        sources = {}
        for s in stocks:
            if s.data_source:
                sources[s.data_source] = sources.get(s.data_source, 0) + 1

        latest_update = None
        for s in stocks:
            if s.last_price_update:
                if latest_update is None or s.last_price_update > latest_update:
                    latest_update = s.last_price_update

        return {
            "status": "ok",
            "latest_update": latest_update.isoformat() if latest_update else None,
            "stock_count": len(stocks),
            "sources": sources,
            "is_realtime": latest_update is not None and (datetime.utcnow() - latest_update).total_seconds() < 3600,
        }
    finally:
        session.close()
```

- [ ] **Step 2: 注册路由**

在 `backend/api/router.py` 中添加:

```python
from backend.api.endpoints import data

api_router.include_router(data.router, tags=["data"])
```

- [ ] **Step 3: 验证**

```bash
curl -s http://localhost:8000/api/v1/data/freshness | python3 -m json.tool
```

Expected: JSON 含 `status`, `latest_update`, `stock_count`, `sources`, `is_realtime`。

- [ ] **Step 4: Commit**

```bash
git add backend/api/endpoints/data.py backend/api/router.py
git commit -m "feat: add /data/freshness endpoint for data source status"
```

---

### Task D4: Header 动态数据状态栏

**Files:**
- Modify: `frontend/src/components/layout/Header.tsx`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/types/stock.ts`

- [ ] **Step 1: 添加类型和 API**

在 `frontend/src/types/stock.ts` 末尾添加:

```typescript
export interface DataFreshness {
  status: string;
  latest_update: string | null;
  stock_count: number;
  sources: Record<string, number>;
  is_realtime: boolean;
}
```

在 `frontend/src/services/api.ts` 中添加:

```typescript
export function fetchDataFreshness(): Promise<DataFreshness> {
  return get<DataFreshness>("/data/freshness");
}
```

- [ ] **Step 2: 重写 Header.tsx**

```tsx
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fetchDataFreshness, type DataFreshness } from "../../services/api";

export default function Header() {
  const [freshness, setFreshness] = useState<DataFreshness | null>(null);

  useEffect(() => {
    fetchDataFreshness().then(setFreshness).catch(() => {});
    const t = setInterval(() => fetchDataFreshness().then(setFreshness).catch(() => {}), 60000);
    return () => clearInterval(t);
  }, []);

  const isLive = freshness?.is_realtime;
  const updateTime = freshness?.latest_update
    ? new Date(freshness.latest_update).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <motion.header
      className="px-5 pt-3 pb-2"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2.5">
          <h1 className="m-0 text-[28px] font-bold tracking-[-0.40px]"
            style={{ fontFamily: '"SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif' }}>
            鲸灵宝
          </h1>
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide"
            style={{
              background: "linear-gradient(135deg, rgba(10,132,255,0.20), rgba(94,92,230,0.20))",
              color: "var(--blue)", border: "0.5px solid rgba(10,132,255,0.25)",
            }}>
            AI
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-full text-[12px] font-medium"
          style={{
            background: isLive ? "rgba(48,209,88,0.12)" : "rgba(255,159,10,0.12)",
            color: isLive ? "var(--green)" : "var(--orange)",
          }}>
          <span className={`w-1.5 h-1.5 rounded-full ${isLive ? "bg-[#30D158] animate-pulse" : "bg-[#FF9F0A]"}`} />
          {isLive && updateTime ? `实时 · ${updateTime}` : updateTime ? `收盘 · ${updateTime}` : "等待数据"}
        </div>
      </div>
      <p className="m-0 mt-1 text-[13px] text-[#98989D]">AI深度选股 · 如鲸探宝</p>
    </motion.header>
  );
}
```

- [ ] **Step 3: 验证**

确保后端运行中，前端编译无报错:

```bash
cd /Users/kunbetter/git/StockRec/frontend && npx tsc --noEmit 2>&1 | head -20
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/Header.tsx frontend/src/services/api.ts frontend/src/types/stock.ts
git commit -m "feat: dynamic data freshness status bar in Header"
```

---

### Task D5: 重新播种数据并验证

- [ ] **Step 1: 重新运行种子脚本**

```bash
.venv/bin/python3 scripts/seed_demo_data.py
```

- [ ] **Step 2: 验证数据时效 API**

```bash
curl -s http://localhost:8000/api/v1/data/freshness | python3 -m json.tool
```

- [ ] **Step 3: Commit (if needed)**

Phase D 完成标记。

---

## Phase A: 布局紧凑性 + AI-First

### Task A1: 扩展类型定义和 API 客户端

**Files:**
- Modify: `frontend/src/types/stock.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: 添加新类型**

将 `frontend/src/types/stock.ts` 完整替换为:

```typescript
export interface StockRecommendation {
  symbol: string; name: string;
  current_price: number | null; price_change_pct: number | null;
  predicted_return: number | null;
  momentum_score: number | null; quality_score: number | null;
  sentiment_score: number | null; composite_score: number | null;
  rank: number | null; risk_level: "low" | "medium" | "high" | null;
  market_cap: number | null; holding_period: string | null;
  ai_summary: string | null;
  industry?: string | null; pe?: number | null;
  roe?: number | null; dividend_yield?: number | null;
  data_source?: string | null; last_price_update?: string | null;
}

export interface RiskSection {
  risk_level: "low" | "medium" | "high";
  label: string; description: string;
  stocks: StockRecommendation[];
}

export interface MarketSummary {
  index_name: string; index_value: number | null;
  change_pct: number | null; market_status: string;
}

export interface RecommendationsResponse {
  date: string; generated_at: string | null;
  market_summary: MarketSummary | null;
  sections: RiskSection[];
}

export interface ScoreBreakdown {
  predicted_return?: { value: number; weight: number; contribution: number };
  momentum_score?: { value: number; weight: number; contribution: number };
  quality_score?: { value: number; weight: number; contribution: number };
  sentiment_score?: { value: number; weight: number; contribution: number };
}

export interface AnalysisDetail {
  symbol: string; name: string; date: string;
  composite_score: number | null;
  score_breakdown: ScoreBreakdown | null;
  layer_scores: { layer1_factor: number | null; layer2_ml: number | null; layer3_event: number | null } | null;
  ai_analysis: {
    recommendation: string | null;
    financial: Record<string, unknown>; news: Record<string, unknown>;
    industry: Record<string, unknown>; risk_flags: string[];
  } | null;
  key_metrics: Record<string, unknown> | null;
  peer_rank?: { rank: number; total: number } | null;
}

export interface PeerStock {
  symbol: string; name: string; industry: string;
  composite_score: number | null; pe: number | null; roe: number | null;
}

export interface BriefingResponse {
  date: string; generated_at: string;
  summary: string; highlights: string[];
  market_mood: string;
}

export interface CompareRequest { symbols: string[]; }

export interface CompareResponse {
  columns: { symbol: string; name: string; metrics: Record<string, number | string | null> }[];
  ai_verdict: string | null;
}

export interface ChatRequest { question: string; }

export interface DataFreshness {
  status: string; latest_update: string | null;
  stock_count: number; sources: Record<string, number>;
  is_realtime: boolean;
}

export interface MarketOverviewResponse {
  date: string; indices: IndexItem[]; breadth: MarketBreadth;
  sectors: SectorItem[]; top_gainers: MoverItem[]; top_losers: MoverItem[];
}
export interface IndexItem { name: string; code: string; value: number; change_pct: number; change_amount: number; }
export interface MarketBreadth { up: number; down: number; flat: number; up_pct: number; down_pct: number; volume_billion: number; limit_up: number; limit_down: number; }
export interface SectorItem { name: string; change_pct: number; leader: string; leader_change: number; }
export interface MoverItem { symbol: string; name: string; change_pct: number; }
export interface WatchlistItem { symbol: string; name: string; industry: string | null; market_cap: number | null; current_price: number | null; price_change_pct: number | null; composite_score: number | null; risk_level: string | null; }
export interface WatchlistResponse { count: number; items: WatchlistItem[]; }
export interface HistoryItem { symbol: string; name: string; trade_date: string | null; composite_score: number | null; predicted_return: number | null; risk_level: string | null; rank: number | null; ai_summary: string | null; }
export interface SystemStatus { last_update: string | null; stock_count: number; watchlist_count: number; database_ok: boolean; recent_jobs: { job_name: string; status: string; started_at: string | null; duration_ms: number | null }[]; }
```

- [ ] **Step 2: 重写 api.ts**

将 `frontend/src/services/api.ts` 完整替换为:

```typescript
import type { RecommendationsResponse, AnalysisDetail, BriefingResponse, CompareRequest, CompareResponse, ChatRequest, DataFreshness, MarketOverviewResponse, IndexItem, MarketBreadth, SectorItem, MoverItem, WatchlistItem, WatchlistResponse, HistoryItem, SystemStatus } from "../types/stock";

const BASE = "/api/v1";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => { if (v !== undefined) url.searchParams.set(k, v); });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface RecParams { date?: string; price_min?: number; price_max?: number; limit?: number; sort_by?: string; sort_order?: string; industry?: string; pe_min?: number; pe_max?: number; dividend_min?: number; risk_level?: string; }

export function fetchRecommendations(params?: RecParams): Promise<RecommendationsResponse> {
  const q: Record<string, string> = {};
  if (params) Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null) q[k] = String(v); });
  return get<RecommendationsResponse>("/recommendations", q);
}

export function fetchBriefing(): Promise<BriefingResponse> {
  return get<BriefingResponse>("/recommendations/briefing");
}

export function fetchStockAnalysis(symbol: string, date?: string): Promise<AnalysisDetail> {
  return get<AnalysisDetail>(`/analysis/${symbol}`, date ? { target_date: date } : {});
}

export function fetchPeers(symbol: string): Promise<{ symbol: string; peers: import("../types/stock").PeerStock[] }> {
  return get(`/recommendations/${symbol}/peers`);
}

export function fetchCompare(symbols: string[]): Promise<CompareResponse> {
  return post<CompareResponse>("/stocks/compare", { symbols } as CompareRequest);
}

export function checkHealth(): Promise<boolean> {
  return get<{ status: string }>("/health").then(d => d.status === "ok").catch(() => false);
}

export function fetchMarketOverview(): Promise<MarketOverviewResponse> {
  return get<MarketOverviewResponse>("/market/overview");
}

export function fetchWatchlist(): Promise<WatchlistResponse> { return get<WatchlistResponse>("/profile/watchlist"); }
export function addToWatchlist(symbol: string): Promise<{ success: boolean; symbol: string }> { return post(`/profile/watchlist/${symbol}`); }
export function removeFromWatchlist(symbol: string): Promise<{ success: boolean; symbol: string }> { return del(`/profile/watchlist/${symbol}`); }
export function fetchRecommendationHistory(limit?: number): Promise<HistoryItem[]> { return get<HistoryItem[]>(`/profile/history?limit=${limit || 30}`); }
export function fetchSystemStatus(): Promise<SystemStatus> { return get<SystemStatus>("/profile/status"); }
export function fetchDataFreshness(): Promise<DataFreshness> { return get<DataFreshness>("/data/freshness"); }
```

- [ ] **Step 3: 验证类型检查**

```bash
cd /Users/kunbetter/git/StockRec/frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: 可能有未使用导入警告（新增类型尚未被引用），无类型错误。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types/stock.ts frontend/src/services/api.ts
git commit -m "feat: extend types and API client for AI-first redesign"
```

---

### Task A2: AIBriefingCard 组件

**Files:**
- Create: `frontend/src/components/home/AIBriefingCard.tsx`

- [ ] **Step 1: 创建组件**

```bash
mkdir -p /Users/kunbetter/git/StockRec/frontend/src/components/home
```

```tsx
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fetchBriefing, type BriefingResponse } from "../../services/api";

export default function AIBriefingCard() {
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBriefing()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) return null;

  return (
    <motion.div
      className="mx-4 mb-3 rounded-[14px] p-3"
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: "linear-gradient(135deg, rgba(10,132,255,0.06), rgba(94,92,230,0.04))",
        border: "0.5px solid rgba(10,132,255,0.12)",
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[14px]">🤖</span>
        <span className="text-[12px] font-semibold text-[#C7C7CC]">今日AI市场简报</span>
        <span className="ml-auto text-[9px] text-[#636366]">
          {new Date(data.generated_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })} 更新
        </span>
      </div>
      <p className="text-[11px] leading-relaxed m-0 text-[#98989D] line-clamp-3">{data.summary}</p>
      {data.highlights && data.highlights.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {data.highlights.map((h, i) => (
            <span key={i} className="text-[9px] px-2 py-0.5 rounded-full"
              style={{ background: "rgba(10,132,255,0.1)", color: "#0A84FF" }}>
              {h}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
```

- [ ] **Step 2: 验证编译**

```bash
cd /Users/kunbetter/git/StockRec/frontend && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/home/AIBriefingCard.tsx
git commit -m "feat: AIBriefingCard component for market summary"
```

---

### Task A3: ViewToggle 组件

**Files:**
- Create: `frontend/src/components/home/ViewToggle.tsx`

- [ ] **Step 1: 创建组件**

```tsx
import { motion } from "framer-motion";

interface ViewToggleProps {
  view: "featured" | "list";
  onChange: (v: "featured" | "list") => void;
  total: number;
}

export default function ViewToggle({ view, onChange, total }: ViewToggleProps) {
  return (
    <div className="flex items-center gap-3 px-4 mb-3">
      <div className="flex rounded-lg p-0.5" style={{ background: "rgba(118,118,128,0.16)" }}>
        {(["featured", "list"] as const).map((v) => (
          <motion.button
            key={v}
            onClick={() => onChange(v)}
            className="relative px-4 py-1.5 rounded-[7px] text-[11px] font-semibold"
            whileTap={{ scale: 0.95 }}
            animate={{ color: view === v ? "#FFFFFF" : "#8E8E93" }}
          >
            {view === v && (
              <motion.div className="absolute inset-0 rounded-[7px] bg-[#0A84FF]"
                layoutId="viewToggle" transition={{ type: "spring", stiffness: 400, damping: 30 }} />
            )}
            <span className="relative z-10">{v === "featured" ? "精选" : "列表"}</span>
          </motion.button>
        ))}
      </div>
      <span className="text-[11px] text-[#636366]">{total}只</span>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/home/ViewToggle.tsx
git commit -m "feat: ViewToggle component for featured/list switch"
```

---

### Task A4: CompactStockCard 和 StarPick 组件

**Files:**
- Create: `frontend/src/components/home/CompactStockCard.tsx`
- Create: `frontend/src/components/home/StarPick.tsx`

- [ ] **Step 1: 创建 CompactStockCard**

```tsx
import { motion } from "framer-motion";
import type { StockRecommendation } from "../../types/stock";

interface CompactStockCardProps {
  stock: StockRecommendation;
  rank: number;
  onTap: (symbol: string) => void;
}

const scoreColor = (s: number) => s >= 70 ? "#30D158" : s >= 50 ? "#FF9F0A" : "#FF453A";
const riskBg: Record<string, string> = { low: "rgba(48,209,88,.12)", medium: "rgba(255,159,10,.12)", high: "rgba(255,69,58,.12)" };
const riskColor: Record<string, string> = { low: "#30D158", medium: "#FF9F0A", high: "#FF453A" };
const riskLabel: Record<string, string> = { low: "低", medium: "中", high: "高" };

export default function CompactStockCard({ stock, rank, onTap }: CompactStockCardProps) {
  const sc = stock.composite_score ?? 0;
  const risk = stock.risk_level || "medium";

  return (
    <motion.div
      className="mx-4 mb-1 rounded-[10px] cursor-pointer spring-press"
      onClick={() => onTap(stock.symbol)}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: rank * 0.03, duration: 0.3 }}
      style={{ background: "rgba(44,44,46,0.6)" }}
    >
      <div className="flex items-center gap-2 px-3 py-2">
        <span className="text-[11px] font-bold w-5 text-center" style={{ color: rank <= 3 ? scoreColor(sc) : "#636366" }}>
          {rank}
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-[12px] font-semibold truncate">{stock.name}</span>
            <span className="text-[8px] px-1.5 py-0.5 rounded-sm font-medium"
              style={{ background: riskBg[risk], color: riskColor[risk] }}>
              {riskLabel[risk]}
            </span>
          </div>
          <span className="text-[9px] text-[#636366]">{stock.symbol} · {stock.industry || "未知"}</span>
        </div>
        <span className="text-[12px] font-bold w-8 text-center" style={{ color: scoreColor(sc) }}>{sc.toFixed(0)}</span>
        <div className="text-right w-16">
          <div className="text-[11px] font-semibold tabular-nums">¥{stock.current_price?.toFixed(2) ?? "-"}</div>
          <div className="text-[9px] font-semibold tabular-nums" style={{ color: (stock.price_change_pct ?? 0) >= 0 ? "#30D158" : "#FF453A" }}>
            {(stock.price_change_pct ?? 0) >= 0 ? "+" : ""}{stock.price_change_pct?.toFixed(2) ?? "-"}%
          </div>
        </div>
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 2: 创建 StarPick**

```tsx
import { motion } from "framer-motion";
import type { StockRecommendation } from "../../types/stock";

interface StarPickProps {
  stock: StockRecommendation;
  onTap: (symbol: string) => void;
}

export default function StarPick({ stock, onTap }: StarPickProps) {
  return (
    <motion.div
      className="mx-4 mb-2 rounded-[14px] p-3 cursor-pointer spring-press"
      onClick={() => onTap(stock.symbol)}
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      style={{
        background: "linear-gradient(135deg, rgba(255,159,10,0.10), rgba(255,159,10,0.02))",
        border: "0.5px solid rgba(255,159,10,0.20)",
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[15px]">⭐</span>
          <span className="text-[13px] font-bold">今日之星</span>
        </div>
        <span className="text-[10px] text-[#FF9F0A] font-semibold">#1 综合评分</span>
      </div>
      <div className="flex items-center justify-between">
        <div>
          <span className="text-[15px] font-bold">{stock.name}</span>
          <span className="text-[10px] text-[#8E8E93] ml-2">{stock.symbol} · {stock.industry || ""}</span>
          <div className="flex gap-3 mt-1">
            <span className="text-[9px] text-[#636366]">PE <b className="text-[#C7C7CC]">{stock.pe ?? "-"}</b></span>
            <span className="text-[9px] text-[#636366]">ROE <b className="text-[#C7C7CC]">{stock.roe?.toFixed(1) ?? "-"}%</b></span>
            <span className="text-[9px] text-[#636366]">股息率 <b className="text-[#C7C7CC]">{stock.dividend_yield?.toFixed(1) ?? "-"}%</b></span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-[30px] font-bold tracking-tight" style={{ color: "#FF9F0A" }}>
            {stock.composite_score?.toFixed(0) ?? "-"}
          </div>
          <div className="text-[12px] font-semibold">¥{stock.current_price?.toFixed(2) ?? "-"}</div>
          <div className="text-[10px] font-semibold" style={{ color: (stock.price_change_pct ?? 0) >= 0 ? "#30D158" : "#FF453A" }}>
            {(stock.price_change_pct ?? 0) >= 0 ? "+" : ""}{stock.price_change_pct?.toFixed(2) ?? "-"}%
          </div>
        </div>
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 3: 验证编译**

```bash
cd /Users/kunbetter/git/StockRec/frontend && npx tsc --noEmit 2>&1 | head -10
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/home/CompactStockCard.tsx frontend/src/components/home/StarPick.tsx
git commit -m "feat: CompactStockCard and StarPick components"
```

---

### Task A5: StockTable 组件

**Files:**
- Create: `frontend/src/components/home/StockTable.tsx`

- [ ] **Step 1: 创建组件**

```tsx
import { useState } from "react";
import { motion } from "framer-motion";
import type { StockRecommendation } from "../../types/stock";

interface StockTableProps {
  stocks: StockRecommendation[];
  onCompare: (symbols: string[]) => void;
  onTap: (symbol: string) => void;
}

type SortKey = "composite_score" | "price_change_pct" | "predicted_return";

export default function StockTable({ stocks, onCompare, onTap }: StockTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("composite_score");
  const [sortAsc, setSortAsc] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc); else { setSortKey(key); setSortAsc(false); }
  };

  const sorted = [...stocks].sort((a, b) => {
    const va = a[sortKey] ?? 0; const vb = b[sortKey] ?? 0;
    return sortAsc ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
  });

  const toggleSelect = (symbol: string) => {
    const next = new Set(selected);
    if (next.has(symbol)) next.delete(symbol); else if (next.size < 5) next.add(symbol);
    setSelected(next);
  };

  const sortArrow = (key: SortKey) => sortKey === key ? (sortAsc ? " ▲" : " ▼") : "";

  return (
    <div>
      <div className="flex px-4 py-1.5 text-[9px] text-[#636366] border-b border-[rgba(255,255,255,0.04)]">
        <span className="w-6">#</span>
        <span className="flex-1">名称</span>
        <button onClick={() => toggleSort("composite_score")} className="w-10 text-center text-[#0A84FF]">评分{sortArrow("composite_score")}</button>
        <span className="w-12 text-right">价格</span>
        <button onClick={() => toggleSort("price_change_pct")} className="w-10 text-right">涨跌{sortArrow("price_change_pct")}</button>
        <button onClick={() => toggleSort("predicted_return")} className="w-10 text-right">预测{sortArrow("predicted_return")}</button>
        <span className="w-6 text-center">☐</span>
      </div>
      {sorted.map((s, i) => {
        const sc = s.composite_score ?? 0;
        const chg = s.price_change_pct ?? 0;
        const ret = s.predicted_return ?? 0;
        return (
          <motion.div key={s.symbol}
            className="flex items-center px-4 py-2 text-[10px] cursor-pointer"
            style={{ background: i % 2 === 0 ? "rgba(44,44,46,0.3)" : "transparent", borderRadius: 6 }}
            onClick={() => onTap(s.symbol)}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.02 }}
          >
            <span className="w-6 text-[#636366] font-bold">{i + 1}</span>
            <span className="flex-1 font-semibold truncate">{s.name}</span>
            <span className="w-10 text-center font-bold" style={{ color: sc >= 70 ? "#30D158" : sc >= 50 ? "#FF9F0A" : "#FF453A" }}>{sc.toFixed(0)}</span>
            <span className="w-12 text-right tabular-nums">¥{s.current_price?.toFixed(2) ?? "-"}</span>
            <span className="w-10 text-right font-semibold tabular-nums" style={{ color: chg >= 0 ? "#30D158" : "#FF453A" }}>{chg >= 0 ? "+" : ""}{chg.toFixed(2)}%</span>
            <span className="w-10 text-right font-semibold tabular-nums" style={{ color: ret >= 0 ? "#30D158" : "#FF453A" }}>{ret >= 0 ? "+" : ""}{ret.toFixed(1)}%</span>
            <span className="w-6 text-center cursor-pointer" onClick={(e) => { e.stopPropagation(); toggleSelect(s.symbol); }}>
              <span style={{ color: selected.has(s.symbol) ? "#0A84FF" : "#636366" }}>{selected.has(s.symbol) ? "☑" : "☐"}</span>
            </span>
          </motion.div>
        );
      })}
      {selected.size > 0 && (
        <div className="px-4 pt-2">
          <motion.button
            className="w-full py-2.5 rounded-xl text-[12px] font-bold text-white"
            style={{ background: "#0A84FF" }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onCompare([...selected])}
          >
            对比选中 ({selected.size})
          </motion.button>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/home/StockTable.tsx
git commit -m "feat: StockTable component with sort, multi-select, compare"
```

---

### Task A6: QuickActions 组件

**Files:**
- Create: `frontend/src/components/home/QuickActions.tsx`

- [ ] **Step 1: 创建组件**

```tsx
import { motion } from "framer-motion";

interface QuickActionsProps {
  onAIChat: () => void;
  onAnalysis: () => void;
}

export default function QuickActions({ onAIChat, onAnalysis }: QuickActionsProps) {
  return (
    <div className="flex gap-2.5 px-4 mt-3 mb-2">
      <motion.button
        onClick={onAIChat}
        className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl text-left"
        style={{ background: "rgba(10,132,255,0.08)", border: "0.5px solid rgba(10,132,255,0.12)" }}
        whileTap={{ scale: 0.96 }}
      >
        <span className="text-[18px]">💬</span>
        <div>
          <div className="text-[11px] font-semibold text-[#0A84FF]">AI 选股问答</div>
          <div className="text-[9px] text-[#636366]">问任何股票相关问题</div>
        </div>
      </motion.button>
      <motion.button
        onClick={onAnalysis}
        className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl text-left"
        style={{ background: "rgba(94,92,230,0.08)", border: "0.5px solid rgba(94,92,230,0.12)" }}
        whileTap={{ scale: 0.96 }}
      >
        <span className="text-[18px]">🔍</span>
        <div>
          <div className="text-[11px] font-semibold text-[#5E5CE6]">深度分析</div>
          <div className="text-[9px] text-[#636366]">财务+财报+行业</div>
        </div>
      </motion.button>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/home/QuickActions.tsx
git commit -m "feat: QuickActions component for AI chat and deep analysis entry"
```

---

### Task A7: 重写 App.tsx 主架构

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/sections/RiskSection.tsx` (不再使用)

- [ ] **Step 1: 重写 App.tsx**

```tsx
import { useState, useCallback, lazy, Suspense } from "react";
import Header from "./components/layout/Header";
import TabBar from "./components/layout/TabBar";
import StatusBar from "./components/layout/StatusBar";
import AIBriefingCard from "./components/home/AIBriefingCard";
import ViewToggle from "./components/home/ViewToggle";
import CompactStockCard from "./components/home/CompactStockCard";
import StarPick from "./components/home/StarPick";
import StockTable from "./components/home/StockTable";
import QuickActions from "./components/home/QuickActions";
import LoadingSkeleton from "./components/common/LoadingSkeleton";
import ErrorState from "./components/common/ErrorState";
import EmptyState from "./components/common/EmptyState";
import { useStocks } from "./hooks/useStocks";
import type { RecParams } from "./services/api";

const MarketPage = lazy(() => import("./components/pages/MarketPage"));
const ProfilePage = lazy(() => import("./components/pages/ProfilePage"));
const StockAnalysis = lazy(() => import("./components/analysis/StockAnalysis"));
const AIChatPage = lazy(() => import("./components/chat/AIChatPage"));
const ComparePage = lazy(() => import("./components/compare/ComparePage"));

function PageLoader() {
  return (
    <div className="px-5 pt-4 space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background: "rgba(255,255,255,0.04)" }} />
      ))}
    </div>
  );
}

type Page = "home" | "market" | "profile" | "analysis" | "ai-chat" | "compare";

function App() {
  const [tab, setTab] = useState("recommend");
  const [page, setPage] = useState<Page>("home");
  const [viewMode, setViewMode] = useState<"featured" | "list">(() =>
    (localStorage.getItem("stockrec_view") as "featured" | "list") || "featured"
  );
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [compareSymbols, setCompareSymbols] = useState<string[]>([]);
  const { data, loading, error, refetch } = useStocks();

  const allStocks = data?.sections.flatMap(s => s.stocks) ?? [];

  const handleViewChange = (v: "featured" | "list") => {
    setViewMode(v);
    localStorage.setItem("stockrec_view", v);
  };

  const handleStockTap = (symbol: string) => {
    setSelectedSymbol(symbol);
    setPage("analysis");
  };

  const handleCompare = (symbols: string[]) => {
    setCompareSymbols(symbols);
    setPage("compare");
  };

  const goHome = () => setPage("home");

  // Sub-page routing
  if (page === "analysis" && selectedSymbol) {
    return (
      <Suspense fallback={<PageLoader />}>
        <StockAnalysis symbol={selectedSymbol} onBack={goHome} />
      </Suspense>
    );
  }
  if (page === "ai-chat") {
    return (
      <Suspense fallback={<PageLoader />}>
        <AIChatPage onBack={goHome} />
      </Suspense>
    );
  }
  if (page === "compare" && compareSymbols.length > 0) {
    return (
      <Suspense fallback={<PageLoader />}>
        <ComparePage symbols={compareSymbols} onBack={goHome} />
      </Suspense>
    );
  }

  return (
    <>
      <StatusBar />
      <div className="phone-content">
        <Header />

        {tab === "recommend" && (
          <>
            {loading && <LoadingSkeleton />}
            {error && <ErrorState message={error} onRetry={() => refetch()} />}
            {!loading && !error && allStocks.length === 0 && <EmptyState />}
            {!loading && !error && allStocks.length > 0 && (
              <>
                <AIBriefingCard />
                <ViewToggle view={viewMode} onChange={handleViewChange} total={allStocks.length} />
                {viewMode === "featured" ? (
                  <>
                    <StarPick stock={allStocks[0]} onTap={handleStockTap} />
                    {allStocks.slice(1).map((s, i) => (
                      <CompactStockCard key={s.symbol} stock={s} rank={i + 2} onTap={handleStockTap} />
                    ))}
                    <QuickActions onAIChat={() => setPage("ai-chat")} onAnalysis={() => {}} />
                  </>
                ) : (
                  <StockTable stocks={allStocks} onCompare={handleCompare} onTap={handleStockTap} />
                )}
              </>
            )}
          </>
        )}

        {tab === "market" && (
          <Suspense fallback={<PageLoader />}><MarketPage /></Suspense>
        )}
        {tab === "profile" && (
          <Suspense fallback={<PageLoader />}><ProfilePage /></Suspense>
        )}

        <TabBar active={tab} onChange={setTab} />
      </div>
    </>
  );
}

export default App;
```

- [ ] **Step 2: 验证编译**

```bash
cd /Users/kunbetter/git/StockRec/frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: 可能有未实现的页面组件的导入错误（将在后续任务创建）。

- [ ] **Step 3: 暂时注释掉未创建的页面导入以通过编译**

在后续任务创建 StockAnalysis、AIChatPage、ComparePage 之前，用内联占位替代 lazy import:

```tsx
// 临时占位，将在 Phase B/C 替换
function StockAnalysisDummy({ symbol, onBack }: { symbol: string; onBack: () => void }) {
  return <div className="p-5 text-white">分析页: {symbol} <button onClick={onBack} className="text-blue-500 ml-3">返回</button></div>;
}
function AIChatPageDummy({ onBack }: { onBack: () => void }) {
  return <div className="p-5 text-white">AI问答 <button onClick={onBack} className="text-blue-500 ml-3">返回</button></div>;
}
function ComparePageDummy({ symbols, onBack }: { symbols: string[]; onBack: () => void }) {
  return <div className="p-5 text-white">对比: {symbols.join(", ")} <button onClick={onBack} className="text-blue-500 ml-3">返回</button></div>;
}
```

然后直接使用这些组件替代 lazy import。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: rewrite App.tsx with AI-first layout and page routing"
```

---

### Task A8: 后端 Briefing API 端点

**Files:**
- Modify: `backend/api/endpoints/recommendations.py`

- [ ] **Step 1: 在 recommendations.py 末尾添加 briefing 端点**

```python
@router.get("/recommendations/briefing")
def get_briefing(request: Request):
    session = get_session()
    try:
        latest = (
            session.query(Recommendation.trade_date)
            .order_by(Recommendation.trade_date.desc())
            .first()
        )
        trade_date = str(latest[0]) if latest else str(date.today())

        recs = (
            session.query(Recommendation)
            .filter(Recommendation.trade_date == trade_date)
            .order_by(Recommendation.composite_score.desc())
            .limit(10)
            .all()
        )

        # Build summary from top recommendations
        top_names = []
        top_industries = set()
        for rec in recs:
            s = session.query(Stock).filter(Stock.symbol == rec.symbol).first()
            if s:
                top_names.append(s.name)
                if s.industry:
                    top_industries.add(s.industry)

        low_count = sum(1 for r in recs if r.risk_level == "low")

        template = (
            f"大盘选股信号更新：今日共追踪{len(recs)}只标的，"
            f"其中低风险{low_count}只。"
            f"资金重点关注{', '.join(list(top_industries)[:4])}等板块。"
            f"AI精选TOP3：{', '.join(top_names[:3])}，"
            f"综合评分领先，防御属性突出。"
        )

        return {
            "date": trade_date,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": template,
            "highlights": list(top_industries)[:4],
            "market_mood": "偏谨慎" if low_count >= recs else "中性",
        }
    finally:
        session.close()
```

- [ ] **Step 2: 验证**

```bash
curl -s http://localhost:8000/api/v1/recommendations/briefing | python3 -m json.tool
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/endpoints/recommendations.py
git commit -m "feat: add /recommendations/briefing AI market summary endpoint"
```

---

### Task A9: 后端 Recommendations 端点扩展排序/筛选参数

**Files:**
- Modify: `backend/api/endpoints/recommendations.py`

- [ ] **Step 1: 修改 get_recommendations 函数签名**

在现有 `get_recommendations` 中添加 `sort_by`, `sort_order`, `industry`, `pe_min`, `pe_max`, `dividend_min`, `risk_level` 参数:

```python
@router.get("/recommendations")
def get_recommendations(
    request: Request,
    target_date: Optional[str] = None,
    limit: int = Query(30, ge=10, le=50),
    price_min: Optional[float] = Query(None),
    price_max: Optional[float] = Query(None),
    sort_by: Optional[str] = Query(None, description="composite_score, price_change_pct, predicted_return"),
    sort_order: Optional[str] = Query("desc"),
    industry: Optional[str] = Query(None),
    pe_min: Optional[float] = Query(None),
    pe_max: Optional[float] = Query(None),
    dividend_min: Optional[float] = Query(None),
    risk_level: Optional[str] = Query(None, description="low, medium, high"),
):
    session = get_session()
    try:
        # ... existing date resolution logic ...

        query = session.query(Recommendation).filter(Recommendation.trade_date == trade_date)
        if price_min is not None:
            query = query.filter(Recommendation.current_price >= price_min)
        if price_max is not None:
            query = query.filter(Recommendation.current_price <= price_max)
        if risk_level is not None:
            query = query.filter(Recommendation.risk_level == risk_level)

        # Industry filter: join with Stock table
        if industry is not None:
            query = query.join(Stock, Recommendation.symbol == Stock.symbol).filter(Stock.industry == industry)

        # Sort
        sort_col = getattr(Recommendation, sort_by, None) if sort_by else None
        if sort_col is not None:
            query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())
        else:
            query = query.order_by(Recommendation.composite_score.desc())

        recs = query.limit(limit).all()

        # ... rest unchanged (stock_repo, grouping, response) ...
```

注意：需要在现有函数体内修改，保留已有的 stock_repo、分组、返回逻辑不变。

- [ ] **Step 2: 验证**

```bash
curl -s "http://localhost:8000/api/v1/recommendations?sort_by=price_change_pct&sort_order=desc&limit=5" | python3 -c "import sys,json;d=json.load(sys.stdin);[print(s['name'],s['price_change_pct']) for sec in d['sections'] for s in sec['stocks']]"
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/endpoints/recommendations.py
git commit -m "feat: add sort, filter params to recommendations endpoint"
```

---

## Phase B: AI 透明度

### Task B1: LayerBreakdown 组件

**Files:**
- Create: `frontend/src/components/analysis/LayerBreakdown.tsx`

- [ ] **Step 1: 创建组件**

```bash
mkdir -p /Users/kunbetter/git/StockRec/frontend/src/components/analysis
```

```tsx
interface LayerBreakdownProps {
  layerScores: { layer1_factor: number | null; layer2_ml: number | null; layer3_event: number | null } | null;
}

const layers = [
  { key: "layer1_factor", label: "Layer 1 · 多因子模型", weight: "60%", color: "#0A84FF", tags: ["动量", "价值", "质量", "成长", "波动"] },
  { key: "layer2_ml", label: "Layer 2 · 机器学习预测", weight: "30%", color: "#5E5CE6", tags: ["LightGBM · 5年数据 · 128维特征"] },
  { key: "layer3_event", label: "Layer 3 · 事件驱动", weight: "10%", color: "#FF9F0A", tags: ["财报", "回购", "分红", "公告"] },
] as const;

export default function LayerBreakdown({ layerScores }: LayerBreakdownProps) {
  if (!layerScores) return null;

  return (
    <div className="glass-card p-4 mb-4">
      <div className="text-[12px] font-semibold text-[#C7C7CC] mb-3">三层评分引擎</div>
      {layers.map((l) => {
        const score = layerScores[l.key as keyof typeof layerScores] ?? 0;
        const pct = Math.min(100, Math.max(0, score));
        return (
          <div key={l.key} className="mb-3 last:mb-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-semibold" style={{ color: l.color }}>{l.label}</span>
              <span className="text-[9px] text-[#8E8E93]">权重 {l.weight}</span>
            </div>
            <div className="h-1 rounded-full mb-2" style={{ background: "rgba(255,255,255,0.06)" }}>
              <div className="h-full rounded-full transition-all duration-600" style={{ width: `${pct}%`, background: l.color }} />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {l.tags.map((t) => (
                <span key={t} className="px-2 py-0.5 rounded-md text-[8px]" style={{ background: `${l.color}14`, color: l.color }}>
                  {t}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/analysis/LayerBreakdown.tsx
git commit -m "feat: LayerBreakdown component showing three-layer engine"
```

---

### Task B2: ContributionChart + AIAnalysis + PeerComparison

**Files:**
- Create: `frontend/src/components/analysis/ContributionChart.tsx`
- Create: `frontend/src/components/analysis/AIAnalysis.tsx`
- Create: `frontend/src/components/analysis/PeerComparison.tsx`

- [ ] **Step 1: ContributionChart.tsx**

```tsx
import type { ScoreBreakdown } from "../../types/stock";

const labelMap: Record<string, string> = {
  predicted_return: "预期收益", momentum_score: "动量趋势",
  quality_score: "基本面质量", sentiment_score: "AI情绪",
};

export default function ContributionChart({ breakdown, total }: { breakdown: ScoreBreakdown | null; total: number }) {
  if (!breakdown) return null;
  const entries = Object.entries(breakdown).filter(([, v]) => v.value > 0);

  return (
    <div className="glass-card p-4 mb-4">
      <div className="text-[12px] font-semibold text-[#C7C7CC] mb-3">分数构成 · 贡献拆解</div>
      <div className="flex items-end gap-2 h-16 mb-3">
        {entries.map(([key, item]) => {
          const h = Math.max(4, (item.contribution / Math.max(total, 1)) * 100);
          return (
            <div key={key} className="flex-1 text-center">
              <div className="rounded-t-sm mx-auto" style={{
                height: `${Math.max(4, h)}%`,
                minHeight: 4,
                background: `linear-gradient(180deg, #0A84FF, rgba(10,132,255,0.3))`,
                width: "70%",
              }} />
              <div className="text-[7px] text-[#636366] mt-1">{labelMap[key] || key}</div>
            </div>
          );
        })}
      </div>
      {entries.map(([key, item]) => (
        <div key={key} className="flex justify-between text-[10px] py-1" style={{ borderBottom: "0.5px solid rgba(255,255,255,0.04)" }}>
          <span className="text-[#98989D]">{labelMap[key] || key} <span className="text-[#636366]">({(item.weight * 100).toFixed(0)}%)</span></span>
          <span className="font-semibold text-[#C7C7CC]">{item.contribution.toFixed(1)}</span>
        </div>
      ))}
      <div className="text-right text-[11px] font-bold text-[#30D158] mt-2">= {total.toFixed(1)}</div>
    </div>
  );
}
```

- [ ] **Step 2: AIAnalysis.tsx**

```tsx
interface AIAnalysisProps {
  recommendation: string | null;
  risk_flags: string[];
}

export default function AIAnalysis({ recommendation, risk_flags }: AIAnalysisProps) {
  if (!recommendation && risk_flags.length === 0) return null;

  return (
    <div className="glass-card p-4 mb-4" style={{ border: "0.5px solid rgba(10,132,255,0.10)" }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[13px]">🤖</span>
        <span className="text-[12px] font-semibold text-[#C7C7CC]">AI 深度分析</span>
        <span className="ml-auto text-[8px] text-[#636366]">Powered by DeepSeek</span>
      </div>
      {recommendation && (
        <p className="text-[11px] leading-relaxed m-0 mb-3 text-[#98989D]">{recommendation}</p>
      )}
      {risk_flags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {risk_flags.map((f, i) => (
            <span key={i} className="px-2 py-1 rounded-md text-[9px]" style={{ background: "rgba(255,69,58,0.08)", color: "#FF453A" }}>
              ⚠ {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: PeerComparison.tsx**

```tsx
import { useState, useEffect } from "react";
import { fetchPeers } from "../../services/api";
import type { PeerStock } from "../../types/stock";

interface PeerComparisonProps { symbol: string; }

export default function PeerComparison({ symbol }: PeerComparisonProps) {
  const [peers, setPeers] = useState<PeerStock[]>([]);

  useEffect(() => {
    fetchPeers(symbol).then(d => setPeers(d.peers || [])).catch(() => {});
  }, [symbol]);

  if (peers.length === 0) return null;

  return (
    <div className="glass-card p-4 mb-4">
      <div className="text-[12px] font-semibold text-[#C7C7CC] mb-3">同行业对比</div>
      <div className="flex text-[9px] text-[#636366] px-2 mb-1">
        <span className="flex-1">名称</span><span className="w-10 text-center">评分</span><span className="w-10 text-right">PE</span><span className="w-10 text-right">ROE</span>
      </div>
      {peers.map((p) => (
        <div key={p.symbol} className="flex items-center px-2 py-1.5 rounded-md text-[10px]"
          style={{ background: p.symbol === symbol ? "rgba(48,209,88,0.06)" : "transparent" }}>
          <span className="flex-1 font-medium" style={{ color: p.symbol === symbol ? "#30D158" : "#8E8E93" }}>{p.name}</span>
          <span className="w-10 text-center font-semibold" style={{ color: (p.composite_score ?? 0) >= 70 ? "#30D158" : "#8E8E93" }}>{p.composite_score?.toFixed(0) ?? "-"}</span>
          <span className="w-10 text-right text-[#8E8E93]">{p.pe ?? "-"}</span>
          <span className="w-10 text-right text-[#8E8E93]">{p.roe?.toFixed(1) ?? "-"}%</span>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/analysis/ContributionChart.tsx frontend/src/components/analysis/AIAnalysis.tsx frontend/src/components/analysis/PeerComparison.tsx
git commit -m "feat: ContributionChart, AIAnalysis, PeerComparison analysis components"
```

---

### Task B3: StockAnalysis 页面

**Files:**
- Create: `frontend/src/components/analysis/StockAnalysis.tsx`

- [ ] **Step 1: 创建页面组件**

```tsx
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchStockAnalysis } from "../../services/api";
import type { AnalysisDetail } from "../../types/stock";
import LayerBreakdown from "./LayerBreakdown";
import ContributionChart from "./ContributionChart";
import AIAnalysis from "./AIAnalysis";
import PeerComparison from "./PeerComparison";
import RiskBadge from "../stocks/RiskBadge";

interface StockAnalysisProps { symbol: string; onBack: () => void; }

const scoreBg = "radial-gradient(ellipse 80% 80% at 50% 20%, rgba(10,132,255,0.18) 0%, transparent 70%)";

export default function StockAnalysis({ symbol, onBack }: StockAnalysisProps) {
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchStockAnalysis(symbol)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [symbol]);

  return (
    <div className="absolute inset-0 z-50 overflow-y-auto" style={{ background: "#000000" }}>
      <motion.div
        className="sticky top-0 z-10 px-5 py-4 flex items-center justify-between"
        style={{ background: "rgba(0,0,0,0.86)", backdropFilter: "blur(20px)" }}
      >
        <button onClick={onBack} className="flex items-center gap-1 text-[17px] font-medium text-[#0A84FF]">
          ← 返回
        </button>
        <span className="text-[17px] font-semibold">{data?.name || symbol}</span>
        <div className="w-[50px]" />
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center py-32 text-[#98989D]">加载中...</div>
      ) : data ? (
        <div className="px-4 pb-32">
          {/* Hero Score */}
          <motion.div className="glass-card p-5 mb-5 text-center relative overflow-hidden"
            initial={{ scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <div className="absolute inset-0" style={{ background: scoreBg }} />
            <div className="relative">
              <div className="flex justify-center gap-2 mb-2">
                <span className="text-[13px] text-[#8E8E93]">{data.symbol}</span>
                <RiskBadge level={(data.key_metrics?.risk_level as string) || "medium"} />
              </div>
              {data.peer_rank && (
                <div className="text-[9px] text-[#636366] mb-1">
                  超过 {data.peer_rank.total - data.peer_rank.rank} 只同行业标的
                </div>
              )}
              <div className="text-[64px] font-bold tracking-[-1.5px] bg-gradient-to-b from-[#FFFFFF] to-[#98989D] bg-clip-text text-transparent"
                style={{ WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                {data.composite_score?.toFixed(0) ?? "-"}
              </div>
              <div className="text-[13px] text-[#636366] mt-1">/ 100</div>

              {data.layer_scores && (
                <div className="flex gap-2 mt-4">
                  {[
                    { l: "因子", v: data.layer_scores.layer1_factor, w: "60%", c: "#0A84FF" },
                    { l: "ML", v: data.layer_scores.layer2_ml, w: "30%", c: "#5E5CE6" },
                    { l: "事件", v: data.layer_scores.layer3_event, w: "10%", c: "#FF9F0A" },
                  ].map((x) => (
                    <div key={x.l} className="flex-1 rounded-xl py-2.5" style={{ background: "rgba(255,255,255,0.04)" }}>
                      <div className="text-[10px] text-[#636366]">{x.l}层</div>
                      <div className="text-[14px] font-semibold mt-0.5" style={{ color: x.c }}>{x.v?.toFixed(0) ?? "-"}</div>
                      <div className="text-[9px] text-[#636366]">{x.w}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>

          {/* Key Metrics */}
          {data.key_metrics && (
            <motion.div className="glass-card p-4 mb-4" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[
                  ["预测收益", data.key_metrics.predicted_return, "%", "#30D158"],
                  ["动量", data.key_metrics.momentum_score, "", "#FF9F0A"],
                  ["质量", data.key_metrics.quality_score, "", "#0A84FF"],
                  ["情绪", data.key_metrics.sentiment_score, "", "#5E5CE6"],
                  ["PE", data.key_metrics.pe, "", "#C7C7CC"],
                  ["股息率", data.key_metrics.dividend_yield, "%", "#30D158"],
                ].map(([l, v, s, c]) => (
                  <div key={l as string}>
                    <div className="text-[10px] text-[#636366] mb-1">{l as string}</div>
                    <div className="text-[16px] font-semibold tracking-tight" style={{ color: c as string }}>
                      {typeof v === "number" ? v.toFixed(1) : "-"}{s as string}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          <LayerBreakdown layerScores={data.layer_scores} />
          <ContributionChart breakdown={data.score_breakdown} total={data.composite_score ?? 0} />
          <AIAnalysis
            recommendation={(data.ai_analysis?.recommendation as string) || null}
            risk_flags={data.ai_analysis?.risk_flags || []}
          />
          <PeerComparison symbol={symbol} />
        </div>
      ) : null}
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx 使用真实组件**

移除 dummy 组件，恢复 lazy import:

```tsx
const StockAnalysis = lazy(() => import("./components/analysis/StockAnalysis"));
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/analysis/StockAnalysis.tsx frontend/src/App.tsx
git commit -m "feat: StockAnalysis page with full AI transparency"
```

---

### Task B4: 后端 Peers 端点 + 分析端点扩展

**Files:**
- Modify: `backend/api/endpoints/recommendations.py`
- Modify: `backend/api/endpoints/analysis.py`

- [ ] **Step 1: 添加 peers 端点**

在 `recommendations.py` 中添加:

```python
@router.get("/recommendations/{symbol}/peers")
def get_peers(symbol: str):
    session = get_session()
    try:
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        if not stock:
            raise HTTPException(status_code=404, detail="Stock not found")

        industry = stock.industry
        if not industry:
            return {"symbol": symbol, "peers": []}

        latest = session.query(Recommendation.trade_date).order_by(Recommendation.trade_date.desc()).first()
        trade_date = str(latest[0]) if latest else str(date.today())

        peer_stocks = session.query(Stock).filter(Stock.industry == industry, Stock.symbol != symbol).all()
        peer_symbols = [p.symbol for p in peer_stocks]

        recs = (
            session.query(Recommendation)
            .filter(Recommendation.symbol.in_(peer_symbols), Recommendation.trade_date == trade_date)
            .order_by(Recommendation.composite_score.desc())
            .all()
        )

        peers = []
        for rec in recs:
            rs = session.query(Stock).filter(Stock.symbol == rec.symbol).first()
            peers.append({
                "symbol": rec.symbol,
                "name": rs.name if rs else rec.symbol,
                "industry": industry,
                "composite_score": rec.composite_score,
                "pe": None, "roe": None,
            })

        return {"symbol": symbol, "peers": peers}
    finally:
        session.close()
```

- [ ] **Step 2: 扩展分析端点返回 peer_rank**

在 `analysis.py` 的 `get_analysis` 中，返回前添加 peer_rank 计算:

```python
# 在 return AnalysisResponse(...) 之前添加:
peer_rank_data = None
if s and s.industry:
    latest_date = rec.trade_date
    all_industry_recs = (
        session.query(Recommendation)
        .join(Stock, Recommendation.symbol == Stock.symbol)
        .filter(Stock.industry == s.industry, Recommendation.trade_date == latest_date)
        .order_by(Recommendation.composite_score.desc())
        .all()
    )
    rank_in_industry = next((i + 1 for i, r in enumerate(all_industry_recs) if r.symbol == symbol), None)
    if rank_in_industry is not None:
        peer_rank_data = {"rank": rank_in_industry, "total": len(all_industry_recs)}

# 在 key_metrics 字典中添加 pe, roe, dividend_yield (暂无真实数据，先传 None)
key_metrics_dict = { ... 原有内容 ...,
    "pe": None, "roe": None, "dividend_yield": None,
}

# 在 AnalysisResponse 中添加 peer_rank
return AnalysisResponse( ... peer_rank=peer_rank_data, ...)
```

注意：需要在 `AnalysisResponse` schema 中添加 `peer_rank` 字段。

- [ ] **Step 3: 更新 schemas.py**

```python
class AnalysisResponse(BaseModel):
    symbol: str; name: str; date: date
    composite_score: Optional[float] = None
    score_breakdown: Optional[dict] = None
    layer_scores: Optional[dict] = None
    ai_analysis: Optional[dict] = None
    key_metrics: Optional[dict] = None
    peer_rank: Optional[dict] = None  # 新增
```

- [ ] **Step 4: 验证**

```bash
curl -s http://localhost:8000/api/v1/recommendations/sh600036/peers | python3 -m json.tool
```

- [ ] **Step 5: Commit**

```bash
git add backend/api/endpoints/recommendations.py backend/api/endpoints/analysis.py backend/api/schemas.py
git commit -m "feat: add peers endpoint and peer_rank to analysis"
```

---

## Phase C: 交互升级

### Task C1: AIChatPage 组件

**Files:**
- Create: `frontend/src/components/chat/AIChatPage.tsx`

- [ ] **Step 1: 创建目录和组件**

```bash
mkdir -p /Users/kunbetter/git/StockRec/frontend/src/components/chat
```

```tsx
import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";

interface Message { role: "user" | "ai"; content: string; }

interface AIChatPageProps { onBack: () => void; }

const suggestions = [
  "高股息+低PE有哪些推荐？",
  "宁德时代现在值得入手吗？",
  "帮我对比一下白酒板块的标的",
  "今天AI策略最看好哪个行业？",
];

export default function AIChatPage({ onBack }: AIChatPageProps) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "ai", content: "你好！我是鲸灵宝 AI 助手，基于 DeepSeek 大模型。我可以帮你分析个股、筛选标的、解读市场。试试下面的问题，或者直接问我～" },
  ]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (question: string) => {
    if (!question.trim() || streaming) return;
    const userMsg: Message = { role: "user", content: question };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setStreaming(true);

    const aiMsg: Message = { role: "ai", content: "" };
    setMessages(prev => [...prev, aiMsg]);

    try {
      const res = await fetch("/api/v1/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok || !res.body) throw new Error("Stream not available");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const chunk = line.slice(6);
            if (chunk === "[DONE]") continue;
            setMessages(prev => {
              const next = [...prev];
              next[next.length - 1] = { ...next[next.length - 1], content: next[next.length - 1].content + chunk };
              return next;
            });
          }
        }
      }
    } catch {
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = { ...next[next.length - 1], content: "抱歉，AI 服务暂时不可用，请稍后再试。" };
        return next;
      });
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="absolute inset-0 z-50 flex flex-col" style={{ background: "#000000" }}>
      <div className="sticky top-0 z-10 px-5 py-4 flex items-center justify-between"
        style={{ background: "rgba(0,0,0,0.86)", backdropFilter: "blur(20px)" }}>
        <button onClick={onBack} className="text-[17px] font-medium text-[#0A84FF]">← 返回</button>
        <span className="text-[17px] font-semibold">AI 选股助手</span>
        <span className="text-[10px] text-[#636366]">DeepSeek</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((m, i) => (
          <motion.div key={i} className={`flex ${m.role === "user" ? "justify-end" : "gap-2"}`}
            initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
            {m.role === "ai" && <span className="text-[16px] flex-shrink-0">🤖</span>}
            <div className={`max-w-[80%] px-3 py-2.5 text-[11px] leading-relaxed ${m.role === "user"
              ? "bg-[#0A84FF] text-white rounded-xl rounded-br-sm"
              : "bg-[rgba(44,44,46,0.7)] text-[#C7C7CC] rounded-xl rounded-bl-sm"}`}>
              {m.content || (streaming && i === messages.length - 1 ? "..." : "")}
            </div>
          </motion.div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions (only show before first user message) */}
      {messages.length <= 1 && (
        <div className="px-4 pb-2 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button key={s} onClick={() => send(s)}
              className="px-3 py-1.5 rounded-full text-[9px] text-[#0A84FF] bg-[rgba(10,132,255,0.08)] border border-[rgba(10,132,255,0.12)]">
              {s}
            </button>
          ))}
        </div>
      )}

      <div className="px-4 py-3">
        <div className="flex gap-2 items-center bg-[rgba(44,44,46,0.6)] rounded-2xl px-4 py-2">
          <span className="text-[16px]">💬</span>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send(input)}
            placeholder="问任何选股问题..."
            className="flex-1 bg-transparent border-none outline-none text-[13px] text-white placeholder-[#636366]"
          />
          <button onClick={() => send(input)} disabled={streaming}
            className="w-6 h-6 rounded-full bg-[#0A84FF] text-white text-[12px] flex items-center justify-center disabled:opacity-40">
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx**

将 `AIChatPageDummy` 替换为 lazy import:

```tsx
const AIChatPage = lazy(() => import("./components/chat/AIChatPage"));
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/chat/AIChatPage.tsx frontend/src/App.tsx
git commit -m "feat: AIChatPage with SSE streaming from DeepSeek"
```

---

### Task C2: AI Chat SSE 后端端点

**Files:**
- Create: `backend/api/endpoints/ai.py`
- Modify: `backend/api/router.py`
- Modify: `backend/ai/deepseek_client.py`

- [ ] **Step 1: 在 deepseek_client.py 添加 chat_stream 方法**

```python
from typing import AsyncIterator

async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
    async with self._semaphore:
        elapsed = datetime.utcnow().timestamp() - self._last_call_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        try:
            stream = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            self._last_call_time = datetime.utcnow().timestamp()
        except Exception as e:
            logger.error(f"DeepSeek stream error: {e}")
            yield ""
```

注意：此方法添加到 `DeepSeekClient` 类内部。

- [ ] **Step 2: 创建 ai.py 端点**

```python
import json
from datetime import date

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.ai.deepseek_client import DeepSeekClient
from backend.persistence.database import get_session
from backend.persistence.models import Recommendation, Stock

router = APIRouter()


class ChatRequest(BaseModel):
    question: str


@router.post("/ai/chat")
async def ai_chat(body: ChatRequest, request: Request):
    config = request.app.state.config
    client = DeepSeekClient(
        api_key=config.ai.api_key,
        base_url=config.ai.base_url,
        model=config.ai.model,
        max_tokens=config.ai.max_tokens,
        temperature=config.ai.temperature,
        max_concurrent=config.ai.rate_limit.max_concurrent,
    )

    session = get_session()
    context_parts = []
    try:
        latest = session.query(Recommendation.trade_date).order_by(Recommendation.trade_date.desc()).first()
        trade_date = str(latest[0]) if latest else str(date.today())
        top_recs = (
            session.query(Recommendation)
            .filter(Recommendation.trade_date == trade_date)
            .order_by(Recommendation.composite_score.desc())
            .limit(10).all()
        )
        for rec in top_recs:
            s = session.query(Stock).filter(Stock.symbol == rec.symbol).first()
            name = s.name if s else rec.symbol
            context_parts.append(
                f"{name}({rec.symbol}): 评分{rec.composite_score:.0f}, "
                f"风险{rec.risk_level}, 预测收益{rec.predicted_return:.1f}%"
            )
    finally:
        session.close()

    context = "\n".join(context_parts)

    system_prompt = (
        "你是鲸灵宝AI选股助手，基于DeepSeek大模型。你的回答基于量化因子模型（60%）、"
        "机器学习预测（30%）和事件驱动分析（10%）的三层选股引擎。"
        "回答风格：专业、简洁、数据驱动。用中文回复。"
        f"\n\n当前Top10推荐标的：\n{context}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": body.question},
    ]

    async def generate():
        async for token in client.chat_stream(messages):
            yield f"data: {token}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

- [ ] **Step 3: 注册路由**

在 `router.py` 中添加:

```python
from backend.api.endpoints import ai

api_router.include_router(ai.router, tags=["ai"])
```

- [ ] **Step 4: 验证**

```bash
curl -s -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"有哪些高股息的股票？"}' --no-buffer
```

Expected: SSE 流式输出 token。

- [ ] **Step 5: Commit**

```bash
git add backend/api/endpoints/ai.py backend/api/router.py backend/ai/deepseek_client.py
git commit -m "feat: SSE chat endpoint integrated with DeepSeek"
```

---

### Task C3: ComparePage 组件

**Files:**
- Create: `frontend/src/components/compare/ComparePage.tsx`

- [ ] **Step 1: 创建目录和组件**

```bash
mkdir -p /Users/kunbetter/git/StockRec/frontend/src/components/compare
```

```tsx
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fetchCompare } from "../../services/api";
import type { CompareResponse } from "../../types/stock";

interface ComparePageProps { symbols: string[]; onBack: () => void; }

const METRIC_LABELS: Record<string, string> = {
  composite_score: "综合评分", predicted_return: "预测收益", momentum_score: "动量",
  quality_score: "质量", sentiment_score: "情绪", current_price: "价格",
  price_change_pct: "涨跌幅", pe: "PE", roe: "ROE", dividend_yield: "股息率",
  market_cap: "市值", risk_level: "风险等级",
};

const scoreColor = (v: number | null | undefined) =>
  v == null ? "#8E8E93" : v >= 70 ? "#30D158" : v >= 50 ? "#FF9F0A" : "#FF453A";

export default function ComparePage({ symbols, onBack }: ComparePageProps) {
  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCompare(symbols)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [symbols]);

  if (loading) return <div className="p-5 text-center text-[#98989D] pt-20">加载中...</div>;
  if (!data || data.columns.length === 0) return <div className="p-5 text-center text-[#98989D] pt-20">暂无数据</div>;

  const metricKeys = Object.keys(data.columns[0].metrics);

  return (
    <div className="absolute inset-0 z-50 overflow-y-auto" style={{ background: "#000000" }}>
      <div className="sticky top-0 z-10 px-5 py-4 flex items-center justify-between"
        style={{ background: "rgba(0,0,0,0.86)", backdropFilter: "blur(20px)" }}>
        <button onClick={onBack} className="text-[17px] font-medium text-[#0A84FF]">← 返回</button>
        <span className="text-[17px] font-semibold">股票对比</span>
        <span className="text-[10px] text-[#636366]">{data.columns.length}只</span>
      </div>

      <div className="px-2 pb-32">
        {/* Column headers */}
        <div className="flex gap-2 mb-4 px-2 sticky top-14 pt-2" style={{ background: "#000" }}>
          <div className="w-16 flex-shrink-0" />
          {data.columns.map((col, i) => (
            <div key={col.symbol} className="flex-1 text-center rounded-t-xl py-2 px-1"
              style={{ borderBottom: `2px solid ${i === 0 ? "#30D158" : "#8E8E93"}` }}>
              <div className="text-[11px] font-bold text-[#C7C7CC]">{col.name}</div>
              <div className="text-[10px] text-[#636366]">{col.symbol}</div>
            </div>
          ))}
        </div>

        {/* Metric rows */}
        {metricKeys.map((key) => (
          <div key={key} className="flex gap-2 px-2 py-2.5 items-center"
            style={{ borderBottom: "0.5px solid rgba(255,255,255,0.04)" }}>
            <span className="w-16 flex-shrink-0 text-[10px] text-[#636366]">{METRIC_LABELS[key] || key}</span>
            {data.columns.map((col, i) => {
              const val = col.metrics[key];
              const isBest = i === 0;
              return (
                <span key={col.symbol} className="flex-1 text-center text-[11px] font-semibold tabular-nums"
                  style={{ color: isBest && typeof val === "number" ? "#30D158" : "#8E8E93" }}>
                  {val != null ? String(val) : "-"}
                </span>
              );
            })}
          </div>
        ))}

        {/* AI Verdict */}
        {data.ai_verdict && (
          <motion.div className="mx-2 mt-4 p-4 rounded-xl"
            style={{ background: "linear-gradient(135deg, rgba(10,132,255,0.05), rgba(94,92,230,0.05))", border: "0.5px solid rgba(10,132,255,0.1)" }}
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex gap-2 items-center mb-2">
              <span className="text-[13px]">🤖</span>
              <span className="text-[11px] font-semibold text-[#C7C7CC]">AI 对比结论</span>
            </div>
            <p className="text-[11px] leading-relaxed m-0 text-[#98989D]">{data.ai_verdict}</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 更新 App.tsx**

将 dummy 替换为 lazy import:

```tsx
const ComparePage = lazy(() => import("./components/compare/ComparePage"));
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/compare/ComparePage.tsx frontend/src/App.tsx
git commit -m "feat: ComparePage with multi-stock comparison and AI verdict"
```

---

### Task C4: Compare 后端端点

**Files:**
- Modify: `backend/api/endpoints/stocks.py`

- [ ] **Step 1: 添加 compare 端点**

在 `stocks.py` 末尾添加:

```python
from pydantic import BaseModel

class CompareRequest(BaseModel):
    symbols: list[str]


@router.post("/stocks/compare")
def compare_stocks(body: CompareRequest, request: Request):
    config = request.app.state.config
    session = get_session()
    try:
        latest = session.query(Recommendation.trade_date).order_by(Recommendation.trade_date.desc()).first()
        trade_date = str(latest[0]) if latest else str(date.today())

        columns = []
        top_scores = {}

        for symbol in body.symbols:
            rec = session.query(Recommendation).filter(
                Recommendation.symbol == symbol, Recommendation.trade_date == trade_date
            ).first()
            stock = session.query(Stock).filter(Stock.symbol == symbol).first()
            if not rec:
                continue

            metrics = {
                "composite_score": rec.composite_score,
                "predicted_return": rec.predicted_return,
                "momentum_score": rec.momentum_score,
                "quality_score": rec.quality_score,
                "sentiment_score": rec.sentiment_score,
                "current_price": rec.current_price,
                "price_change_pct": rec.price_change_pct,
                "pe": None, "roe": None, "dividend_yield": None,
                "market_cap": rec.market_cap,
                "risk_level": rec.risk_level,
            }
            columns.append({
                "symbol": symbol,
                "name": stock.name if stock else symbol,
                "metrics": metrics,
            })

        # AI verdict
        if len(columns) >= 2:
            names_scores = [(c["name"], c["metrics"]["composite_score"]) for c in columns]
            best = max(names_scores, key=lambda x: x[1] or 0)
            verdict = f"综合评分最高的是{best[0]}（{best[1]:.0f}分）。"
        else:
            verdict = None

        return {"columns": columns, "ai_verdict": verdict}
    finally:
        session.close()
```

注意：`CompareRequest` 可以复用 `backend/api/schemas.py` 中的定义（如果已有）或直接在文件中定义。

- [ ] **Step 2: 验证**

```bash
curl -s -X POST http://localhost:8000/api/v1/stocks/compare \
  -H "Content-Type: application/json" \
  -d '{"symbols":["sh600036","sz002415","sh600519"]}' | python3 -m json.tool
```

- [ ] **Step 3: Commit**

```bash
git add backend/api/endpoints/stocks.py
git commit -m "feat: stock compare endpoint with AI verdict"
```

---

### Task C5: FilterPanel 组件

**Files:**
- Create: `frontend/src/components/filter/FilterPanel.tsx`

- [ ] **Step 1: 创建组件**

```bash
mkdir -p /Users/kunbetter/git/StockRec/frontend/src/components/filter
```

```tsx
import { motion, AnimatePresence } from "framer-motion";

interface FilterPanelProps {
  open: boolean;
  onClose: () => void;
  onApply: (params: Record<string, string>) => void;
}

const PRESETS = [
  { key: "high_dividend", label: "高股息", desc: "股息率 > 3%" },
  { key: "low_pe", label: "低估值", desc: "PE < 15" },
  { key: "high_growth", label: "高成长", desc: "营收增速 > 20%" },
  { key: "high_roe", label: "高ROE", desc: "ROE > 15%" },
  { key: "low_volatility", label: "低波动", desc: "低beta" },
  { key: "breakout", label: "强势突破", desc: "突破60日高点" },
];

export default function FilterPanel({ open, onClose, onApply }: FilterPanelProps) {
  const [selectedRisks, setSelectedRisks] = useState<Set<string>>(new Set());
  const [selectedPresets, setSelectedPresets] = useState<Set<string>>(new Set());

  const toggleRisk = (r: string) => {
    const next = new Set(selectedRisks); next.has(r) ? next.delete(r) : next.add(r); setSelectedRisks(next);
  };
  const togglePreset = (p: string) => {
    const next = new Set(selectedPresets); next.has(p) ? next.delete(p) : next.add(p); setSelectedPresets(next);
  };

  const handleApply = () => {
    const params: Record<string, string> = {};
    if (selectedRisks.size > 0) params.risk_level = [...selectedRisks].join(",");
    onApply(params);
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="absolute inset-0 z-50" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose} style={{ background: "rgba(0,0,0,0.6)" }}>
          <motion.div className="absolute bottom-0 left-0 right-0 rounded-t-[24px] p-5 pb-8"
            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }} transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
            style={{ background: "#1C1C1E" }}>
            <div className="w-8 h-1 rounded-full bg-[#636366] mx-auto mb-4" />

            <div className="text-[16px] font-bold mb-4">筛选</div>

            <div className="mb-5">
              <div className="text-[11px] font-semibold text-[#98989D] mb-2">风险等级</div>
              <div className="flex gap-2">
                {["low", "medium", "high"].map((r) => (
                  <button key={r} onClick={() => toggleRisk(r)} className="px-4 py-2 rounded-full text-[11px] font-medium"
                    style={{ background: selectedRisks.has(r) ? "#0A84FF" : "rgba(118,118,128,0.16)", color: selectedRisks.has(r) ? "#fff" : "#8E8E93" }}>
                    {{ low: "低风险", medium: "中风险", high: "高风险" }[r]}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-5">
              <div className="text-[11px] font-semibold text-[#98989D] mb-2">预置策略</div>
              <div className="flex flex-wrap gap-2">
                {PRESETS.map((p) => (
                  <button key={p.key} onClick={() => togglePreset(p.key)} className="px-3 py-1.5 rounded-full text-[10px]"
                    style={{ background: selectedPresets.has(p.key) ? "rgba(10,132,255,0.15)" : "rgba(255,255,255,0.05)", color: selectedPresets.has(p.key) ? "#0A84FF" : "#8E8E93", border: selectedPresets.has(p.key) ? "0.5px solid rgba(10,132,255,0.3)" : "none" }}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={handleApply} className="w-full py-3 rounded-xl bg-[#0A84FF] text-white text-[14px] font-bold">
              应用筛选
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

- [ ] **Step 2: 集成到 App.tsx**

在 App.tsx 的推荐 tab 中添加 FilterPanel（放在 ViewToggle 旁边加一个筛选按钮触发）：

```tsx
const [filterOpen, setFilterOpen] = useState(false);
// ... 在 ViewToggle 旁边添加筛选按钮
// ... 底部添加 <FilterPanel open={filterOpen} onClose={() => setFilterOpen(false)} onApply={...} />
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/filter/FilterPanel.tsx
git commit -m "feat: FilterPanel with presets and risk level filtering"
```

---

### Task C6: 集成 FilterPanel 到 App.tsx + 最终清理

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 更新 App.tsx 集成筛选面板**

在 ViewToggle 行添加筛选按钮:

```tsx
// 在 ViewToggle 的同一行右侧添加一个筛选按钮
<div className="flex items-center px-4 mb-3">
  <ViewToggle view={viewMode} onChange={handleViewChange} total={allStocks.length} />
  <button onClick={() => setFilterOpen(true)}
    className="ml-auto px-3 py-1.5 rounded-lg text-[10px] font-medium"
    style={{ background: "rgba(118,118,128,0.16)", color: "#8E8E93" }}>
    筛选 ▾
  </button>
</div>
```

同时在 App 组件底部（return 之前）添加:

```tsx
<FilterPanel open={filterOpen} onClose={() => setFilterOpen(false)}
  onApply={(params) => {
    setFilterOpen(false);
    refetch(params as RecParams);
  }} />
```

添加 import:

```tsx
import FilterPanel from "./components/filter/FilterPanel";
import { useState } from "react"; // 确保已有
```

- [ ] **Step 2: 移除旧组件文件**

```bash
# 不再使用的组件可以保留（不影响功能），或删除
# git rm frontend/src/components/sections/RiskSection.tsx
# git rm frontend/src/components/stocks/StockCard.tsx
# git rm frontend/src/components/analysis/AnalysisModal.tsx
```

建议先保留以备回滚，后续再清理。

- [ ] **Step 3: 最终验证**

```bash
cd /Users/kunbetter/git/StockRec/frontend && npx tsc --noEmit 2>&1
```

确保无类型错误。如有，修复。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: integrate FilterPanel into main view"
```

---

## 验证 Checkpoint

全部任务完成后，执行以下验证:

```bash
# 1. 后端测试
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
curl -s http://localhost:8000/api/v1/data/freshness | python3 -m json.tool
curl -s http://localhost:8000/api/v1/recommendations/briefing | python3 -m json.tool
curl -s http://localhost:8000/api/v1/recommendations?sort_by=price_change_pct | python3 -m json.tool | head -10

# 2. 前端编译
cd frontend && npx tsc --noEmit

# 3. 浏览器验证
# 打开 http://localhost:5173
# 验证: AI简报卡片显示、精选/列表切换、头部显示实时状态
# 点击股票卡片 → 分析页（三层引擎+贡献图+同行业对比）
# 切到列表视图 → 多选 → 对比
# 点击 AI 问答 → 输入问题 → 流式回复
```
