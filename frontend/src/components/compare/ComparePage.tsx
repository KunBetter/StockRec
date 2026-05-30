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

        {metricKeys.map((key) => (
          <div key={key} className="flex gap-2 px-2 py-2.5 items-center"
            style={{ borderBottom: "0.5px solid rgba(255,255,255,0.04)" }}>
            <span className="w-16 flex-shrink-0 text-[10px] text-[#636366]">{METRIC_LABELS[key] || key}</span>
            {data.columns.map((col) => {
              const val = col.metrics[key];
              return (
                <span key={col.symbol} className="flex-1 text-center text-[11px] font-semibold tabular-nums"
                  style={{ color: "#8E8E93" }}>
                  {val != null ? String(val) : "-"}
                </span>
              );
            })}
          </div>
        ))}

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
