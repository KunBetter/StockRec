import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  fetchWatchlist, addToWatchlist, removeFromWatchlist,
  fetchRecommendationHistory, fetchSystemStatus,
  type WatchlistItem, type HistoryItem, type SystemStatus,
} from "../../services/api";
import RiskBadge from "../stocks/RiskBadge";

export default function ProfilePage() {
  const [tab, setTab] = useState<"watchlist" | "history" | "system">("watchlist");
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchWatchlist(), fetchRecommendationHistory(30), fetchSystemStatus(),
    ]).then(([w, h, s]) => {
      setWatchlist(w.items); setHistory(h); setStatus(s);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="px-5 pt-4 space-y-3">
      {[1, 2, 3].map((i) => <div key={i} className="h-16 rounded-xl animate-pulse" style={{ background: "rgba(255,255,255,0.04)" }} />)}
    </div>;
  }

  return (
    <motion.div
      className="px-5 pb-6"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Sub-tabs */}
      <div className="flex gap-2 mb-5 pt-2 overflow-x-auto">
        {(["watchlist", "history", "system"] as const).map((k) => (
          <motion.button
            key={k}
            onClick={() => setTab(k)}
            className="px-4 py-2 rounded-full text-[13px] font-semibold whitespace-nowrap"
            whileTap={{ scale: 0.95 }}
            animate={{
              background: tab === k ? "var(--blue)" : "rgba(118,118,128,0.14)",
              color: tab === k ? "#FFFFFF" : "#98989D",
            }}
          >
            {{ watchlist: "自选", history: "历史", system: "系统" }[k]}
          </motion.button>
        ))}
      </div>

      {/* Watchlist */}
      {tab === "watchlist" && (
        <section>
          <div className="text-[17px] font-semibold mb-3">自选股 · {watchlist.length}</div>
          {watchlist.length === 0 && (
            <div className="glass-card p-10 text-center">
              <div className="text-4xl mb-3">★</div>
              <p className="text-[14px] font-medium mb-1 text-[#98989D]">暂无自选股</p>
              <p className="text-[12px] text-[#636366]">在推荐页点击股票可添加到自选</p>
            </div>
          )}
          {watchlist.map((item) => (
            <motion.div
              key={item.symbol}
              className="glass-card p-4 mb-2 flex items-center justify-between"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-[14px] font-semibold truncate">{item.name}</span>
                  {item.risk_level && <RiskBadge level={item.risk_level} />}
                </div>
                <span className="text-[11px] text-[#636366]">{item.symbol} · {item.industry || "未知"}</span>
              </div>
              <div className="text-right ml-3">
                <div className="stat-number text-[16px]">¥{item.current_price?.toFixed(2) ?? "-"}</div>
                {item.price_change_pct != null && (
                  <div className="text-[12px] font-semibold" style={{ color: item.price_change_pct >= 0 ? "#30D158" : "#FF453A" }}>
                    {item.price_change_pct >= 0 ? "+" : ""}{item.price_change_pct.toFixed(2)}%
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </section>
      )}

      {/* History */}
      {tab === "history" && (
        <section>
          <div className="text-[17px] font-semibold mb-3">推荐历史</div>
          {history.length === 0 && (
            <div className="glass-card p-10 text-center text-[#98989D]">暂无记录</div>
          )}
          {history.map((item) => (
            <div key={`${item.symbol}-${item.trade_date}`} className="glass-card p-3.5 mb-2">
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-semibold">{item.name}</span>
                  {item.risk_level && <RiskBadge level={item.risk_level} />}
                </div>
                <span className="text-[11px] text-[#636366]">{item.trade_date}</span>
              </div>
              <div className="flex items-center gap-4 text-[11px] text-[#8E8E93]">
                <span>评分 <b className="text-[13px] text-[#C7C7CC]">{item.composite_score?.toFixed(0) ?? "-"}</b></span>
                <span>排名 <b className="text-[#C7C7CC]">{item.rank ?? "-"}</b></span>
                {item.predicted_return != null && (
                  <span style={{ color: item.predicted_return >= 0 ? "#30D158" : "#FF453A" }}>
                    预测 {(item.predicted_return >= 0 ? "+" : "")}{item.predicted_return.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </section>
      )}

      {/* System */}
      {tab === "system" && status && (
        <section className="space-y-4">
          <div className="text-[17px] font-semibold mb-1">系统状态</div>
          <div className="glass-card p-4">
            <div className="grid grid-cols-2 gap-5">
              {[
                ["追踪股票", status.stock_count],
                ["自选股", status.watchlist_count],
                ["最新数据", status.last_update || "暂无"],
              ].map(([l, v]) => (
                <div key={l as string}>
                  <div className="text-[10px] text-[#636366] mb-1">{l as string}</div>
                  <div className="text-[20px] font-bold stat-number">{String(v)}</div>
                </div>
              ))}
              <div>
                <div className="text-[10px] text-[#636366] mb-1">数据库</div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: status.database_ok ? "#30D158" : "#FF453A" }} />
                  <span className="text-[14px] font-semibold">{status.database_ok ? "正常" : "异常"}</span>
                </div>
              </div>
            </div>
          </div>

          {status.recent_jobs.length > 0 && (
            <>
              <div className="text-[14px] font-semibold mt-3 mb-2">最近任务</div>
              <div className="glass-card overflow-hidden">
                {status.recent_jobs.map((job, idx) => (
                  <div key={idx} className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "0.5px solid rgba(255,255,255,0.04)" }}>
                    <div className="flex items-center gap-2.5">
                      <span className="w-1.5 h-1.5 rounded-full" style={{ background: job.status === "success" ? "#30D158" : job.status === "failed" ? "#FF453A" : "#FF9F0A" }} />
                      <span className="text-[12px] text-[#C7C7CC]">{job.job_name}</span>
                    </div>
                    <span className="text-[10px] text-[#636366]">{job.duration_ms ? `${(job.duration_ms / 1000).toFixed(1)}s` : ""}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </section>
      )}
    </motion.div>
  );
}
