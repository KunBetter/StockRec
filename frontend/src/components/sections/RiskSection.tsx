import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { StockRecommendation } from "../../types/stock";
import StockCard from "../stocks/StockCard";

interface RiskSectionProps {
  label: string; description: string; riskLevel: string;
  stocks: StockRecommendation[]; onStockTap: (symbol: string) => void;
}

const headerMeta: Record<string, { color: string; glow: string; label: string; desc: string }> = {
  low: { color: "#30D158", glow: "rgba(48,209,88,0.20)", label: "低风险", desc: "稳健增长 · 适合长期持有" },
  medium: { color: "#FF9F0A", glow: "rgba(255,159,10,0.20)", label: "中风险", desc: "成长均衡 · 适合中期配置" },
  high: { color: "#FF453A", glow: "rgba(255,69,58,0.20)", label: "高风险", desc: "高弹性 · 适合短线博弈" },
};

interface RiskTabsProps {
  sections: { risk_level: string; label: string; description: string; stocks: StockRecommendation[] }[];
  onStockTap: (symbol: string) => void;
}

export default function RiskTabs({ sections, onStockTap }: RiskTabsProps) {
  const [active, setActive] = useState(0);
  const levels = ["low", "medium", "high"];
  const activeLevel = levels[active];

  const sectionMap: Record<string, StockRecommendation[]> = {};
  sections.forEach((s) => { sectionMap[s.risk_level] = s.stocks; });

  const activeStocks = sectionMap[activeLevel] || [];
  const meta = headerMeta[activeLevel] || headerMeta.medium;

  return (
    <div>
      {/* Segmented Control */}
      <div className="px-4 pt-2 pb-3">
        <div
          className="flex rounded-xl p-0.5"
          style={{ background: "rgba(118,118,128,0.16)" }}
        >
          {levels.map((level, i) => {
            const m = headerMeta[level];
            const isActive = i === active;
            const count = sectionMap[level]?.length || 0;
            return (
              <motion.button
                key={level}
                onClick={() => setActive(i)}
                className="relative flex-1 py-2.5 rounded-[10px] text-[14px] font-semibold z-10"
                whileTap={{ scale: 0.96 }}
                animate={{ color: isActive ? "#FFFFFF" : "#8E8E93" }}
                transition={{ duration: 0.2 }}
              >
                {isActive && (
                  <motion.div
                    className="absolute inset-0 rounded-[10px]"
                    layoutId="riskSegment"
                    style={{ background: m.color }}
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative z-10 flex items-center justify-center gap-1.5">
                  {m.label}
                  <span className="text-[11px] opacity-60">{count}</span>
                </span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Description */}
      <motion.div
        className="px-5 pb-3 text-center"
        key={activeLevel}
        initial={{ opacity: 0, y: -4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <p className="text-[12px] m-0 text-[#8E8E93]">{meta.desc}</p>
      </motion.div>

      {/* Stock Cards */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeLevel}
          initial={{ opacity: 0, x: active > levels.indexOf(activeLevel) ? 40 : -40 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: active > levels.indexOf(activeLevel) ? -40 : 40 }}
          transition={{ duration: 0.25, ease: [0.25, 0.1, 0.25, 1] }}
        >
          {activeStocks.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-[#636366]">
              <div className="text-3xl mb-3">--</div>
              <p className="text-[13px]">该风险等级暂无推荐</p>
            </div>
          )}
          {activeStocks.map((stock, i) => (
            <StockCard key={stock.symbol} stock={stock} onTap={onStockTap} index={i} />
          ))}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// Keep legacy export for backward compat
export function RiskSectionSection({ label, description, riskLevel, stocks, onStockTap }: RiskSectionProps) {
  if (stocks.length === 0) return null;
  const meta = headerMeta[riskLevel] || headerMeta.medium;
  return (
    <section className="mb-1">
      <div className="flex items-baseline gap-2.5 px-5 pt-3 pb-2">
        <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ background: meta.color, boxShadow: `0 0 8px ${meta.glow}` }} />
        <span className="text-[17px] font-semibold">{label}</span>
        <span className="text-[13px] text-[#98989D]">{stocks.length}只</span>
      </div>
      {stocks.map((stock, i) => (
        <StockCard key={stock.symbol} stock={stock} onTap={onStockTap} index={i} />
      ))}
    </section>
  );
}
