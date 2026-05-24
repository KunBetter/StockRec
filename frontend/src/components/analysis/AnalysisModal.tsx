import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { AnalysisDetail } from "../../types/stock";
import { fetchStockAnalysis } from "../../services/api";
import RiskBadge from "../stocks/RiskBadge";

const scoreBg =
  "radial-gradient(ellipse 80% 80% at 50% 20%, rgba(10,132,255,0.18) 0%, transparent 70%)";

export default function AnalysisModal({ symbol, onClose }: { symbol: string | null; onClose: () => void }) {
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    fetchStockAnalysis(symbol)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [symbol]);

  return (
    <AnimatePresence>
      {symbol && (
        <motion.div
          className="absolute inset-0 z-50 overflow-y-auto"
          style={{ background: "#000000" }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.25 }}
        >
          <div>
            <motion.div
              className="sticky top-0 z-10 px-5 py-4 flex items-center justify-between"
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.05, duration: 0.3 }}
              style={{
                background: "rgba(0,0,0,0.86)",
                backdropFilter: "blur(20px)",
                WebkitBackdropFilter: "blur(20px)",
              }}
            >
              <motion.button
                onClick={onClose}
                className="flex items-center gap-1 text-[17px] font-medium"
                style={{ color: "var(--blue)" }}
                whileTap={{ scale: 0.94 }}
              >
                <svg width="10" height="16" viewBox="0 0 10 16"><path d="M9 1L1 8l8 7" stroke="#0A84FF" strokeWidth="2.2" fill="none" strokeLinecap="round"/></svg>
                关闭
              </motion.button>
              <span className="text-[17px] font-semibold">{data?.name || symbol}</span>
              <div className="w-[50px]" />
            </motion.div>

            {loading ? (
              <div className="flex items-center justify-center py-32 text-[#98989D]">加载中...</div>
            ) : data ? (
              <div className="px-4 pb-32">
                {/* Hero Score Card */}
                <motion.div
                  className="glass-card-elevated p-5 mb-5 text-center relative overflow-hidden"
                  initial={{ scale: 0.96, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: 0.1, duration: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
                >
                  <div className="absolute inset-0" style={{ background: scoreBg }} />
                  <div className="relative">
                    <div className="flex justify-center gap-2 mb-2">
                      <span className="text-[13px] text-[#8E8E93]">{data.symbol}</span>
                      <RiskBadge level={(data.key_metrics?.risk_level as string) || "medium"} />
                    </div>
                    <div className="text-[12px] text-[#636366] mb-2">综合评分</div>
                    <div className="stat-number text-[64px] leading-none tracking-[-1.5px] bg-gradient-to-b from-[#FFFFFF] to-[#98989D] bg-clip-text text-transparent" style={{ WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
                      {data.composite_score?.toFixed(0) ?? "-"}
                    </div>
                    <div className="text-[13px] text-[#636366] mt-1">/ 100</div>

                    {data.layer_scores && (
                      <div className="flex gap-2 mt-4">
                        {[
                          { l: "因子", v: data.layer_scores.layer1_factor, w: "60%" },
                          { l: "ML", v: data.layer_scores.layer2_ml, w: "30%" },
                          { l: "事件", v: data.layer_scores.layer3_event, w: "10%" },
                        ].map((x) => (
                          <div key={x.l} className="flex-1 rounded-xl py-2.5" style={{ background: "rgba(255,255,255,0.04)" }}>
                            <div className="text-[10px] text-[#636366]">{x.l}层</div>
                            <div className="text-[14px] font-semibold mt-0.5">{x.v?.toFixed(0) ?? "-"}</div>
                            <div className="text-[9px] text-[#636366]">{x.w}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>

                {/* Key Metrics Grid */}
                {data.key_metrics && (
                  <motion.div
                    className="glass-card p-4 mb-4"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.15, duration: 0.3 }}
                  >
                    <div className="grid grid-cols-4 gap-3 text-center">
                      {[
                        ["预测收益", data.key_metrics.predicted_return as number, "%", "#30D158"],
                        ["动量", data.key_metrics.momentum_score as number, "", "#FF9F0A"],
                        ["质量", data.key_metrics.quality_score as number, "", "#0A84FF"],
                        ["情绪", data.key_metrics.sentiment_score as number, "", "#5E5CE6"],
                      ].map(([l, v, s, c]) => (
                        <div key={l as string}>
                          <div className="text-[10px] text-[#636366] mb-1">{l as string}</div>
                          <div className="stat-number text-[18px] tracking-[-0.24px]" style={{ color: c as string }}>
                            {typeof v === "number" ? v.toFixed(1) : "-"}{s as string}
                          </div>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}

                {/* AI Analysis */}
                {data.ai_analysis && (
                  <motion.div
                    className="glass-card p-4 mb-4"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.3 }}
                  >
                    <h3 className="text-[14px] font-semibold mb-3 text-[#98989D]">AI 分析</h3>
                    {data.ai_analysis.recommendation && (
                      <p className="text-[14px] leading-relaxed m-0 mb-4 text-[#C7C7CC]">
                        {data.ai_analysis.recommendation}
                      </p>
                    )}
                    {data.ai_analysis.risk_flags && data.ai_analysis.risk_flags.length > 0 && (
                      <div>
                        <div className="text-[11px] font-semibold text-[#FF453A] mb-2">风险提示</div>
                        {data.ai_analysis.risk_flags.map((flag: string, i: number) => (
                          <div key={i} className="flex items-start gap-2 mb-1.5">
                            <span className="text-[#FF453A] text-[10px] mt-0.5">●</span>
                            <span className="text-[12px] text-[#8E8E93]">{flag}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}

                {/* Score Breakdown */}
                {data.score_breakdown && (
                  <motion.div
                    className="glass-card p-4 mb-4"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.25, duration: 0.3 }}
                  >
                    <h3 className="text-[14px] font-semibold mb-3 text-[#98989D]">得分明细</h3>
                    {Object.entries(data.score_breakdown).map(([key, item]) => {
                      const labelMap: Record<string, string> = {
                        predicted_return: "预期收益率",
                        momentum_score: "动量趋势",
                        quality_score: "基本面质量",
                        sentiment_score: "AI情绪分析",
                      };
                      return (
                        <div
                          key={key}
                          className="flex items-center justify-between py-2"
                          style={{ borderBottom: "0.5px solid rgba(255,255,255,0.06)" }}
                        >
                          <div className="flex items-baseline gap-2">
                            <span className="text-[13px] text-[#C7C7CC]">{labelMap[key] || key}</span>
                            <span className="text-[10px] text-[#636366]">{(item.weight * 100).toFixed(0)}%</span>
                          </div>
                          <span className="text-[13px] font-semibold tabular-nums text-[#98989D]">
                            {item.contribution.toFixed(1)}
                          </span>
                        </div>
                      );
                    })}
                  </motion.div>
                )}
              </div>
            ) : null}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
