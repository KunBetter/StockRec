#!/usr/bin/env python3
"""Compare two recommendation snapshots and show changes."""
import json
import sys
from datetime import date

def load_snapshot(path):
    with open(path) as f:
        return json.load(f)

def main():
    if len(sys.argv) != 3:
        print("Usage: python scripts/compare_snapshots.py <snapshot1.json> <snapshot2.json>")
        sys.exit(1)

    old = load_snapshot(sys.argv[1])
    new = load_snapshot(sys.argv[2])

    old_stocks = {}
    for sec in old["sections"]:
        for s in sec["stocks"]:
            old_stocks[s["symbol"]] = s

    new_stocks = {}
    for sec in new["sections"]:
        for s in sec["stocks"]:
            new_stocks[s["symbol"]] = s

    old_symbols = set(old_stocks)
    new_symbols = set(new_stocks)
    added = new_symbols - old_symbols
    removed = old_symbols - new_symbols
    common = old_symbols & new_symbols

    # Header
    print("=" * 75)
    print(f"推荐快照对比")
    print(f"  基准: {sys.argv[1]}  ({len(old_stocks)} 只)")
    print(f"  对比: {sys.argv[2]}  ({len(new_stocks)} 只)")
    print("=" * 75)

    # Market
    old_ms = old.get("market_summary", {})
    new_ms = new.get("market_summary", {})
    if old_ms.get("index_value") and new_ms.get("index_value"):
        idx_chg = new_ms["index_value"] - old_ms["index_value"]
        print(f"\n📊 上证指数: {old_ms['index_value']} → {new_ms['index_value']} ({idx_chg:+.2f})")

    # New entries
    if added:
        print(f"\n🆕 新进推荐 ({len(added)}):")
        for sym in sorted(added):
            s = new_stocks[sym]
            print(f"  #{s['rank']:<3} {s['name']:<8s} {sym:<12s} 综合={s['composite_score']:.1f}  风险={s['risk_level']}")

    # Exits
    if removed:
        print(f"\n🚫 退出推荐 ({len(removed)}):")
        for sym in sorted(removed):
            s = old_stocks[sym]
            print(f"  曾#{s['rank']:<3} {s['name']:<8s} {sym:<12s} 曾综合={s['composite_score']:.1f}")

    # Ranking changes
    print(f"\n📈 排名变化 ({len(common)} 只共同股票):")
    print(f"  {'名称':8s} {'排名变化':>8s} {'评分变化':>8s} {'涨跌幅变化':>10s} {'风险变化':>8s}")
    print(f"  {'─'*50}")

    changes = []
    for sym in common:
        o, n = old_stocks[sym], new_stocks[sym]
        rank_delta = (o.get("rank") or 0) - (n.get("rank") or 0)
        score_delta = (n.get("composite_score") or 0) - (o.get("composite_score") or 0)
        pct_delta = (n.get("price_change_pct") or 0) - (o.get("price_change_pct") or 0)
        risk_changed = o.get("risk_level") != n.get("risk_level")
        changes.append((rank_delta, score_delta, pct_delta, risk_changed, o, n))

    changes.sort(key=lambda x: -x[0])  # sort by rank improvement

    for rank_delta, score_delta, pct_delta, risk_changed, o, n in changes:
        rank_str = f"▲{rank_delta}" if rank_delta > 0 else f"▼{abs(rank_delta)}" if rank_delta < 0 else "—"
        score_str = f"+{score_delta:.1f}" if score_delta > 0 else f"{score_delta:.1f}"
        pct_str = f"+{pct_delta:.1f}%" if pct_delta > 0 else f"{pct_delta:.1f}%"
        risk_str = f"{o.get('risk_level')}→{n.get('risk_level')}" if risk_changed else "—"
        print(f"  {n['name']:8s} {rank_str:>8s} {score_str:>8s} {pct_str:>10s} {risk_str:>8s}")

    # Score distribution comparison
    print(f"\n📊 综合评分分布:")
    old_scores = sorted([s["composite_score"] for s in old_stocks.values() if s.get("composite_score")])
    new_scores = sorted([s["composite_score"] for s in new_stocks.values() if s.get("composite_score")])
    if old_scores and new_scores:
        print(f"  基准: min={min(old_scores):.1f}  max={max(old_scores):.1f}  avg={sum(old_scores)/len(old_scores):.1f}")
        print(f"  对比: min={min(new_scores):.1f}  max={max(new_scores):.1f}  avg={sum(new_scores)/len(new_scores):.1f}")

    print()

if __name__ == "__main__":
    main()
