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
