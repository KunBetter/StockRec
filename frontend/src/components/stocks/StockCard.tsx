import { motion } from "framer-motion";
import type { StockRecommendation } from "../../types/stock";
import RiskBadge from "./RiskBadge";
import PriceDisplay from "./PriceDisplay";
import ScoreBar from "./ScoreBar";
import AIAnalysisPreview from "./AIAnalysisPreview";

interface StockCardProps {
  stock: StockRecommendation;
  onTap: (symbol: string) => void;
  index?: number;
}

const riskGradients: Record<string, [string, string]> = {
  low: ["rgba(48,209,88,0.06)", "rgba(48,209,88,0.02)"],
  medium: ["rgba(255,159,10,0.06)", "rgba(255,159,10,0.02)"],
  high: ["rgba(255,69,58,0.06)", "rgba(255,69,58,0.02)"],
};

const scoreColor = (s: number) =>
  s >= 70 ? "#30D158" : s >= 50 ? "#FF9F0A" : "#FF453A";

export default function StockCard({ stock, onTap, index = 0 }: StockCardProps) {
  const [from, to] = riskGradients[stock.risk_level || "medium"] || riskGradients.medium;
  const sc = stock.composite_score ?? 0;

  return (
    <motion.div
      className="glass-card mx-4 mb-2.5 cursor-pointer spring-press"
      onClick={() => onTap(stock.symbol)}
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
      style={{ background: `linear-gradient(180deg, ${from} 0%, ${to} 100%), rgba(44,44,46,0.72)` }}
    >
      <div className="p-4">
        {/* Top: name + score + price */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[16px] font-semibold tracking-[-0.16px] truncate">{stock.name}</span>
              <RiskBadge level={stock.risk_level || "medium"} />
            </div>
            <span className="text-[12px] text-[#8E8E93]">{stock.symbol}</span>
          </div>
          <div className="text-right ml-3 flex items-start gap-3">
            <div className="text-center">
              <div className="text-[10px] text-[#636366] mb-0.5">综合评分</div>
              <div
                className="stat-number text-[26px] tracking-[-0.40px] leading-none"
                style={{
                  color: scoreColor(sc),
                  textShadow: `0 0 16px ${scoreColor(sc)}40`,
                }}
              >
                {stock.composite_score?.toFixed(0) ?? "-"}
              </div>
            </div>
            <div className="pt-0.5">
              <div className="stat-number text-[18px] tracking-[-0.24px] leading-tight">
                ¥{stock.current_price?.toFixed(2) ?? "-"}
              </div>
              <PriceDisplay price={null} change={stock.price_change_pct} />
            </div>
          </div>
        </div>

        {/* Score bars */}
        <div className="space-y-2 mb-3">
          <ScoreBar score={sc} label="综合" />
          <ScoreBar score={stock.momentum_score ?? 0} label="动量" />
          <ScoreBar score={stock.quality_score ?? 0} label="质量" />
        </div>

        {/* Metrics row */}
        <div className="flex items-center justify-between text-[11px] mb-2.5 text-[#8E8E93]">
          <span>
            预测收益{" "}
            <b style={{ color: (stock.predicted_return ?? 0) >= 0 ? "#30D158" : "#FF453A" }}>
              {(stock.predicted_return ?? 0) >= 0 ? "+" : ""}{stock.predicted_return?.toFixed(1) ?? "-"}%
            </b>
          </span>
          <span>AI情绪 <b className="text-[#8E8E93]">{stock.sentiment_score?.toFixed(0) ?? "-"}</b></span>
        </div>

        {/* Holding period */}
        {stock.holding_period && (
          <div className="flex items-center gap-2 mb-2.5 py-1.5 px-3 rounded-xl text-[12px]" style={{ background: "rgba(10,132,255,0.10)", color: "var(--blue)" }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <circle cx="6" cy="6" r="5" stroke="#0A84FF" strokeWidth="1.2"/>
              <path d="M6 3v3.5L8.5 8" stroke="#0A84FF" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
            <span className="font-semibold">{stock.holding_period}</span>
          </div>
        )}

        {/* AI summary */}
        <div style={{ borderTop: "0.5px solid rgba(255,255,255,0.06)", paddingTop: 8 }}>
          <AIAnalysisPreview summary={stock.ai_summary} />
        </div>
      </div>
    </motion.div>
  );
}
