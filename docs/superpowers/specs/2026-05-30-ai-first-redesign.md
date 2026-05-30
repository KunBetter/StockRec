# StockRec 鲸灵宝 AI-First 改版设计规范

**日期**: 2026-05-30  
**状态**: 设计完成，待实现  
**优先级**: D → A → B → C

## 设计目标

将当前工具型推荐页面升级为 **AI 优先 + 专业数据双模式** 的选股工具。让 AI 选股能力从后台走到前台，同时保留专业用户需要的高信息密度视图。

## 整体信息架构

```
首页 (推荐 Tab)
├── Header: 标题 + AI标识 + 实时状态
├── AI 简报卡片 (新增)
├── 视图切换: 精选 / 列表
├── 精选视图: 今日之星(置顶) + 紧凑卡片列表
├── 列表视图: 排序表格 + 多选 + 批量对比
└── AI 快捷入口: AI问答 + 深度分析

行情 Tab (保持不变，数据源改为实时)
我的 Tab (保持不变)

新增页面:
├── /analysis/:symbol — 个股深度分析 (重构)
├── /compare — 多股对比 (新增)
├── /ai-chat — AI 选股问答 (新增)
└── /filter — 智能筛选面板 (新增)
```

---

## D: 数据准确度 (优先级 1 — 基础)

### 目标
将当前静态 demo 数据替换为来自真实数据源的行情数据。

### 后端改动

**1. 实时价格获取**
- 激活现有 `backend/data/` 下的数据源客户端 (akshare, baostock, sina, tencent)
- 修改 `backend/scheduler/jobs/hourly_update.py`，调用 `DataOrchestrator` 拉取实时行情
- 降级链: akshare → sina → tencent (任一失败自动切换)
- Redis 缓存实时价格，TTL 60s

**2. K线数据回填**
- 运行 `scripts/backfill_kline.py` 回填近1年日K线
- 写入 `daily_kline` 和 `daily_kline_metadata` 表
- 为 Layer1 因子计算提供真实数据基础

**3. 数据时效性 API**
- 新增 `GET /api/v1/data/freshness` 端点
- 返回各数据源最新更新时间、状态

**4. 数据库模型补充**
- `stocks` 表新增 `last_price_update` 字段
- `stocks` 表新增 `data_source` 字段 (akshare / sina / tencent)

### 前端改动
- 状态栏从静态"市场开放"改为动态"● 实时 · 14:32"或"○ 延迟 · 昨日收盘"
- 每张股票卡片显示数据时效微标 (绿色=实时, 灰色=收盘)
- 新增价格异常标记 (>20% 波动标记为"待确认")

---

## A: 布局紧凑性 + AI-First (优先级 2)

### 目标
首屏可见股票数从 1.5 只提升到 4-6 只，AI 分析内容置顶。

### 前端改动

**1. AI 简报卡片 (新增组件 `AIBriefingCard`)**
- 位置: Header 下方，视图切换上方
- 内容: AI 生成的市场一句话总结 (由 `ai_summary` 扩展，调用 DeepSeek)
- 样式: 蓝色渐变边框，圆角14px，含更新时间戳
- 数据来源: 新增 `GET /api/v1/recommendations/briefing` 端点

**2. 视图切换 (精选/列表双模式)**
- 组件: `ViewToggle` — segmented control 样式
- 状态: 用户偏好存入 localStorage

**3. 精选视图 — 紧凑卡片 (`CompactStockCard`)**
- 今日之星: 评分第1名置顶，卡片略大 (显示PE/ROE/股息率)，金色边框
- 普通卡片: 水平一行式布局，高度约40px
  - 布局: [排名] [名称+风险标签] [行业] [评分] [价格] [涨跌]
  - 点击进入个股分析页
- 原版 `StockCard` 废弃

**4. 列表视图 (`StockTable`)**
- 表格列: #, 名称/行业, 评分▼, 价格, 涨跌, 预测, ☐(多选)
- 支持点击列头排序 (评分/涨跌/预测)
- 底部操作栏: "对比选中(N)"按钮 + 排序下拉
- 多选上限: 5只

**5. 风险筛选改为 Dropdown**
- 移除当前的三段式风险 Tab (占据大量垂直空间)
- 改为列表页的 filter chip: 全部 | 低风险 | 中风险 | 高风险

**6. 底部快捷入口**
- "AI 选股问答" 和 "深度分析" 两个快捷卡片
- 仅在精选视图底部显示

**7. 移除的元素**
- `PriceRangeSelector` 组件 (合并到筛选面板)
- 风险分段式 `RiskTabs` 组件 (改为 filter chips)

### API 改动
- `GET /api/v1/recommendations` 增加 `sort_by` 和 `sort_order` 参数
- 新增 `GET /api/v1/recommendations/briefing` — AI 市场简报

---

## B: AI 透明度 (优先级 3)

### 目标
让用户理解选股评分的来龙去脉，增强对 AI 推荐的信任。

### 前端改动

**1. 个股分析页重构 (`StockAnalysis` 替代原 `AnalysisModal`)**
- 从全屏 Modal 改为独立路由页面 `/analysis/:symbol`
- 内容区块:

**a) 评分 Hero (同原版，保留)**
- 大号综合评分数字 + 百分位描述 ("超过96%标的")

**b) 三层引擎分解 (新增 `LayerBreakdown`)**
- 三行进度条: Layer1因子 / Layer2 ML / Layer3 事件
- 每行显示: 名称 + 权重 + 进度条 (着色: 蓝/紫/橙) + 细分因子标签
- Layer1 因子标签可点击展开，查看每个因子的定义和得分

**c) 贡献瀑布图 (新增 `ContributionChart`)**
- 柱状图: 预期收益、动量、质量、情绪、事件 各贡献多少分
- 带权重标注 (50% / 20% / 20% / 10% / 0%)
- 底部: 合计 = 综合评分

**d) AI 深度分析 (重构 `AIAnalysis`)**
- 结构化输出: 综合分析段落 + 正面因素标签(绿) + 风险提示标签(红)
- 数据来源标注: "Powered by DeepSeek · 基于截至YYYY-MM-DD数据"
- 调用 `ai_full_analysis` 字段 (已在 Recommendation 模型中有此字段)

**e) 同行业对比 (新增 `PeerComparison`)**
- 小型表格: 同行业标的按评分排列
- 列: 名称、评分、PE、ROE
- 当前股票高亮

**f) 关键指标网格 (保留，微调)**
- 原4项 → 扩展为6项: 预测收益、动量、质量、情绪、PE、股息率

### API 改动
- `GET /api/v1/recommendations/{symbol}` 扩展返回字段: `pe`, `roe`, `dividend_yield`, `percentile_rank`
- `GET /api/v1/recommendations/{symbol}/peers` — 同行业标的 (新增)

### 后端改动
- `backend/ai/prompts.py` 增加结构化分析 prompt (输出正面因素列表 + 风险标签列表)
- `backend/ai/recommendation_writer.py` 修改为结构化输出
- `backend/persistence/models.py` Recommendation 表确保 `ai_full_analysis` 和 `ai_risk_flags` 字段完整

---

## C: 交互升级 (优先级 4)

### 目标
增加 AI 对话式交互、多股对比、智能筛选功能。

### 1. AI 选股问答 (`/ai-chat`)

**前端**
- 新增页面组件 `AIChatPage`
- 聊天界面: AI 欢迎消息 + 预置推荐问题 chips
- 用户输入 → API → 流式返回 AI 回复
- AI 回复包含: 文字分析 + 嵌入式股票卡片 (可点击跳转)
- 入口: 首页底部快捷入口 / Tab 栏新增 AI icon

**API**
- `POST /api/v1/ai/chat` — 接收用户问题，调用 DeepSeek，返回 SSE 流式响应
- 请求体: `{ "question": string, "context": { "symbols": [...] } }`
- 响应: SSE stream，每 chunk 一个 token

**后端**
- `backend/ai/deepseek_client.py` 新增 `chat_stream()` 方法
- `backend/api/endpoints/ai.py` 新增 SSE endpoint
- System prompt 包含当前推荐列表摘要和选股策略说明

### 2. 多股对比 (`/compare`)

**前端**
- 新增页面组件 `ComparePage`
- 顶部: 股票选择器 (从自选/推荐中选取，最多5只)
- 对比表格: 指标行 × 股票列，最佳值绿色高亮
- 底部: AI 对比结论卡片 (非流式，一次性返回)
- 入口: 列表视图多选后点击"对比选中" / 个股分析页"加入对比"按钮

**API**
- `POST /api/v1/stocks/compare` — 请求体 `{ "symbols": ["...", "..."] }`
- 返回对比数据 + AI 生成对比结论

**后端**
- 新增 `backend/ai/recommendation_writer.py` 方法 `generate_comparison()`

### 3. 智能筛选面板

**前端**
- 组件 `FilterPanel` — 从底部弹出的 Sheet
- 预置策略 chips: 高股息、低估值、高成长、高ROE、低波动、强势突破、超跌反弹
- 高级筛选: 行业、风险等级、PE范围、股息率、市值范围
- 预置策略对应后端预定义的筛选参数组合

**API**
- `GET /api/v1/recommendations` 扩展筛选参数: `industry`, `pe_min`, `pe_max`, `dividend_min`, `market_cap_min`, `market_cap_max`

### 4. Tab 栏调整
- 新增 AI Tab icon (中间位置): 推荐 | **AI** | 行情 | 我的
- 或保持3Tab结构，AI 入口放在推荐页底部 (推荐后者，避免过度增加导航复杂度)

---

## 数据流

```
实时行情源 (akshare/sina/tencent)
    ↓ DataOrchestrator (降级链)
    ↓ Redis (缓存60s)
    ↓
┌─ FastAPI ───────────────────────┐
│  /recommendations (列表+筛选)     │
│  /recommendations/briefing (AI简报)│
│  /recommendations/:symbol (深度分析)│
│  /recommendations/:symbol/peers  │
│  /stocks/compare (对比)          │
│  /ai/chat (SSE问答)              │
│  /data/freshness (数据时效)      │
└─────────────────────────────────┘
    ↓ HTTP / SSE
React Frontend (Vite + Tailwind)
    ↓
精选/列表双视图 → 分析页 → 对比页 → AI问答
```

## 文件变更清单

### 后端新增/修改
| 文件 | 操作 | 说明 |
|---|---|---|
| `backend/api/endpoints/recommendations.py` | 修改 | 增加筛选/排序参数，新增briefing和peers端点 |
| `backend/api/endpoints/ai.py` | 新增 | AI chat SSE端点 |
| `backend/api/endpoints/stocks.py` | 修改 | 新增compare端点 |
| `backend/api/endpoints/data.py` | 新增 | 数据时效性端点 |
| `backend/api/schemas.py` | 修改 | 新增response schema |
| `backend/scheduler/jobs/hourly_update.py` | 修改 | 接入真实数据源 |
| `backend/ai/deepseek_client.py` | 修改 | 新增chat_stream方法 |
| `backend/ai/recommendation_writer.py` | 修改 | 结构化输出 + 对比生成 |
| `backend/ai/prompts.py` | 修改 | 新prompt模板 |
| `backend/persistence/models.py` | 修改 | 新增字段 |
| `backend/config.py` | 修改 | 新增AI chat配置 |

### 前端新增/修改
| 文件 | 操作 | 说明 |
|---|---|---|
| `frontend/src/App.tsx` | 重写 | 新架构，路由化 |
| `frontend/src/components/layout/Header.tsx` | 修改 | 动态状态栏 |
| `frontend/src/components/home/AIBriefingCard.tsx` | 新增 | AI简报卡片 |
| `frontend/src/components/home/CompactStockCard.tsx` | 新增 | 紧凑卡片 |
| `frontend/src/components/home/StarPick.tsx` | 新增 | 今日之星 |
| `frontend/src/components/home/ViewToggle.tsx` | 新增 | 视图切换 |
| `frontend/src/components/home/StockTable.tsx` | 新增 | 列表视图 |
| `frontend/src/components/home/QuickActions.tsx` | 新增 | AI快捷入口 |
| `frontend/src/components/analysis/StockAnalysis.tsx` | 新增 | 个股分析页 |
| `frontend/src/components/analysis/LayerBreakdown.tsx` | 新增 | 三层引擎 |
| `frontend/src/components/analysis/ContributionChart.tsx` | 新增 | 贡献图 |
| `frontend/src/components/analysis/AIAnalysis.tsx` | 新增 | 结构化AI分析 |
| `frontend/src/components/analysis/PeerComparison.tsx` | 新增 | 同行业对比 |
| `frontend/src/components/compare/ComparePage.tsx` | 新增 | 对比页 |
| `frontend/src/components/chat/AIChatPage.tsx` | 新增 | AI问答 |
| `frontend/src/components/filter/FilterPanel.tsx` | 新增 | 筛选面板 |
| `frontend/src/components/sections/RiskSection.tsx` | 删除 | 不再使用 |
| `frontend/src/components/stocks/StockCard.tsx` | 删除 | 替换为CompactStockCard |
| `frontend/src/components/analysis/AnalysisModal.tsx` | 删除 | 替换为StockAnalysis页面 |
| `frontend/src/services/api.ts` | 修改 | 新增所有API调用 |
| `frontend/src/types/stock.ts` | 修改 | 新增类型定义 |

### 脚本
| 文件 | 操作 | 说明 |
|---|---|---|
| `scripts/backfill_kline.py` | 运行 | 回填K线数据 |

---

## 风险与约束

- **数据源可用性**: akshare/baostock 可能因网络或反爬限制不可用，需确保降级链有效
- **DeepSeek API 速率限制**: AI 问答新增调用量，需监控 token 消耗和 rate limit
- **SQLite 性能**: 当前使用 SQLite，大量K线数据可能影响性能。后续考虑迁移 PostgreSQL
- **移动端 React Native**: 本次改版仅覆盖 Web 前端，移动端需后续同步

## 非目标 (本次不改)

- 移动端 React Native 对齐
- PostgreSQL 迁移
- 用户认证与个性化推荐
- 推送通知
- 实盘交易接口
