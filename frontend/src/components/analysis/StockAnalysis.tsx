import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { fetchStockAnalysis } from "../../services/api";
import type { AnalysisDetail } from "../../types/stock";
import LayerBreakdown from "./LayerBreakdown";
import ContributionChart from "./ContributionChart";
import AIAnalysis from "./AIAnalysis";
import PeerComparison from "./PeerComparison";
import RiskBadge from "../stocks/RiskBadge";

interface StockAnalysisProps { symbol: string; onBack: () => void; }

const scoreBg = "radial-gradient(ellipse 80% 80% at 50% 20%, rgba(10,132,255,0.18) 0%, transparent 70%)";

export default function StockAnalysis({ symbol, onBack }: StockAnalysisProps) {
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchStockAnalysis(symbol)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [symbol]);

  return (
    <div className="absolute inset-0 z-50 overflow-y-auto" style={{ background: "#000000" }}>
      <motion.div
        className="sticky top-0 z-10 px-5 py-4 flex items-center justify-between"
        style={{ background: "rgba(0,0,0,0.86)", backdropFilter: "blur(20px)" }}
      >
        <button onClick={onBack} className="flex items-center gap-1 text-[17px] font-medium text-[#0A84FF]">
          ← 返回
        </button>
        <span className="text-[17px] font-semibold">{data?.name || symbol}</span>
        <div className="w-[50px]" />
      </motion.div>

      {loading ? (
        <div className="flex items-center justify-center py-32 text-[#98989D]">加载中...</div>
      ) : data ? (
        <div className="px-4 pb-32">
          {/* Hero Score */}
          <motion.div className="glass-card p-5 mb-5 text-center relative overflow-hidden"
            initial={{ scale: 0.96, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
            <div className="absolute inset-0" style={{ background: scoreBg }} />
            <div className="relative">
              <div className="flex justify-center gap-2 mb-2">
                <span className="text-[13px] text-[#8E8E93]">{data.symbol}</span>
                <RiskBadge level={(data.key_metrics?.risk_level as string) || "medium"} />
              </div>
              {data.peer_rank && (
                <div className="text-[9px] text-[#636366] mb-1">
                  超过 {data.peer_rank.total - data.peer_rank.rank} 只同行业标的
                </div>
              )}
              <div className="text-[64px] font-bold tracking-[-1.5px] bg-gradient-to-b from-[#FFFFFF] to-[#98989D] bg-clip-text text-transparent"
                style={{ WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                {data.composite_score?.toFixed(0) ?? "-"}
              </div>
              <div className="text-[13px] text-[#636366] mt-1">/ 100</div>

              {data.layer_scores && (
                <div className="flex gap-2 mt-4">
                  {[
                    { l: "因子", v: data.layer_scores.layer1_factor, w: "60%", c: "#0A84FF" },
                    { l: "ML", v: data.layer_scores.layer2_ml, w: "30%", c: "#5E5CE6" },
                    { l: "事件", v: data.layer_scores.layer3_event, w: "10%", c: "#FF9F0A" },
                  ].map((x) => (
                    <div key={x.l} className="flex-1 rounded-xl py-2.5" style={{ background: "rgba(255,255,255,0.04)" }}>
                      <div className="text-[10px] text-[#636366]">{x.l}层</div>
                      <div className="text-[14px] font-semibold mt-0.5" style={{ color: x.c }}>{x.v?.toFixed(0) ?? "-"}</div>
                      <div className="text-[9px] text-[#636366]">{x.w}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>

          {/* Key Metrics */}
          {data.key_metrics && (
            <motion.div className="glass-card p-4 mb-4" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
              <div className="grid grid-cols-3 gap-3 text-center">
                {[
                  ["预测收益", data.key_metrics.predicted_return, "%", "#30D158"],
                  ["动量", data.key_metrics.momentum_score, "", "#FF9F0A"],
                  ["质量", data.key_metrics.quality_score, "", "#0A84FF"],
                  ["情绪", data.key_metrics.sentiment_score, "", "#5E5CE6"],
                  ["PE", data.key_metrics.pe, "", "#C7C7CC"],
                  ["股息率", data.key_metrics.dividend_yield, "%", "#30D158"],
                ].map(([l, v, s, c]) => (
                  <div key={l as string}>
                    <div className="text-[10px] text-[#636366] mb-1">{l as string}</div>
                    <div className="text-[16px] font-semibold tracking-tight" style={{ color: c as string }}>
                      {typeof v === "number" ? v.toFixed(1) : "-"}{s as string}
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          <LayerBreakdown layerScores={data.layer_scores} />
          <ContributionChart breakdown={data.score_breakdown} total={data.composite_score ?? 0} />
          <AIAnalysis
            recommendation={(data.ai_analysis?.recommendation as string) || null}
            risk_flags={data.ai_analysis?.risk_flags || []}
          />
          <PeerComparison symbol={symbol} />
        </div>
      ) : null}
    </div>
  );
}
