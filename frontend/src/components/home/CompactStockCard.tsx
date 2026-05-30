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
