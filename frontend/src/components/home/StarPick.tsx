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
            <span className="text-[9px] text-[#636366]">PE <b className="text-[#C7C7CC]">{stock.pe?.toFixed(1) ?? "-"}</b></span>
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
