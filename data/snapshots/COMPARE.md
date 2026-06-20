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
