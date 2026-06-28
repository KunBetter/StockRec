# 推荐快照对比

用于对比不同日期的推荐结果变化。快照文件命名格式：`recommendations_YYYY-MM-DD.json`

## 对比命令

```bash
source .venv/bin/activate && python3 scripts/compare_snapshots.py \
  data/snapshots/recommendations_2026-06-20.json \
  data/snapshots/recommendations_NEW_DATE.json
```

## 对比维度

| 维度 | 说明 |
|------|------|
| 排名变化 | 同一股票在不同快照中的排名升降 |
| 新增/退出 | 新进入推荐列表 vs 被淘汰 |
| 评分变化 | 综合评分、动量、质量、情绪的量化对比 |
| 风险迁移 | 风险等级（低/中/高）的变化 |
| 价格涨跌 | 期间价格和涨跌幅变化 |
| AI 摘要 | AI 观点的变化 |

---

## 快照清单

| 文件 | 日期 | 内容 |
|------|------|------|
| [returns_top50_2026-06-27.md](returns_top50_2026-06-27.md) | 2026-06-27 | A股近1年涨幅排行 TOP 50（MD格式） |
| [returns_top50_2026-06-27.json](returns_top50_2026-06-27.json) | 2026-06-27 | A股近1年涨幅排行 TOP 50（JSON格式） |
| [recommendations_2026-06-20.json](recommendations_2026-06-20.json) | 2026-06-20 | 当日推荐结果快照 |
| [recommendations_2026-06-20.txt](recommendations_2026-06-20.txt) | 2026-06-20 | 当日推荐结果快照（文本） |
