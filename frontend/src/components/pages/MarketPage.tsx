import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fetchMarketOverview, type MarketOverviewResponse } from "../../services/api";

const indexBg = "radial-gradient(ellipse 80% 80% at 50% 0%, rgba(10,132,255,0.06) 0%, transparent 70%)";

export default function MarketPage() {
  const [data, setData] = useState<MarketOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMarketOverview()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="px-5 pt-4 space-y-4">
      {[1, 2, 3].map((i) => <div key={i} className="h-24 rounded-2xl animate-pulse" style={{ background: "rgba(255,255,255,0.04)" }} />)}
    </div>;
  }
  if (!data) return null;

  return (
    <motion.div
      className="px-5 pb-6 space-y-5"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
    >
      {/* Indices */}
      <section>
        <div className="section-label !pt-0">市场指数</div>
        <div className="grid grid-cols-2 gap-2.5">
          {data.indices.map((idx, i) => (
            <motion.div
              key={idx.code}
              className="glass-card p-3.5 relative overflow-hidden"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06, duration: 0.35 }}
            >
              <div className="absolute inset-0" style={{ background: indexBg }} />
              <div className="relative">
                <div className="text-[11px] text-[#98989D] mb-1.5">{idx.name}</div>
                <div className="stat-number text-[18px] tracking-[-0.24px]">
                  {idx.value.toLocaleString("zh-CN", { minimumFractionDigits: 2 })}
                </div>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-[12px] font-semibold tabular-nums" style={{ color: idx.change_pct >= 0 ? "#30D158" : "#FF453A" }}>
                    {idx.change_pct >= 0 ? "+" : ""}{idx.change_pct.toFixed(2)}%
                  </span>
                  <span className="text-[10px] text-[#636366]">{idx.change_amount >= 0 ? "+" : ""}{idx.change_amount.toFixed(2)}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Breadth */}
      <section>
        <div className="section-label">市场情绪</div>
        <div className="glass-card p-4">
          <div className="flex items-end gap-1.5 mb-4 h-14">
            <motion.div
              className="flex-1 rounded-t-md"
              initial={{ height: 0 }}
              animate={{ height: `${data.breadth.up_pct}%` }}
              transition={{ delay: 0.3, duration: 0.8, ease: "easeOut" }}
              style={{ background: "linear-gradient(180deg, #30D158 0%, rgba(48,209,88,0.3) 100%)", minHeight: 4 }}
            />
            <motion.div
              className="flex-1 rounded-t-md"
              initial={{ height: 0 }}
              animate={{ height: `${data.breadth.down_pct}%` }}
              transition={{ delay: 0.3, duration: 0.8, ease: "easeOut" }}
              style={{ background: "linear-gradient(180deg, #FF453A 0%, rgba(255,69,58,0.3) 100%)", minHeight: 4 }}
            />
          </div>
          <div className="flex justify-between text-[13px] font-semibold">
            <span style={{ color: "#30D158" }}>涨 {data.breadth.up}家</span>
            <span className="text-[#636366]">平 {data.breadth.flat}家</span>
            <span style={{ color: "#FF453A" }}>跌 {data.breadth.down}家</span>
          </div>
          <div className="flex justify-between mt-3 pt-3" style={{ borderTop: "0.5px solid rgba(255,255,255,0.06)" }}>
            {[
              ["成交额", `${data.breadth.volume_billion}亿`],
              ["涨停", "+"+String(data.breadth.limit_up)],
              ["跌停", String(data.breadth.limit_down)],
            ].map(([l, v]) => (
              <div key={l} className="text-center flex-1">
                <div className="text-[10px] text-[#636366] mb-0.5">{l}</div>
                <div className="text-[13px] font-semibold" style={{ color: l === "涨停" ? "#30D158" : l === "跌停" ? "#FF453A" : "#fff" }}>{v}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Sectors */}
      <section>
        <div className="section-label">行业板块</div>
        <div className="glass-card overflow-hidden">
          {data.sectors.slice(0, 8).map((sec, i) => (
            <div
              key={sec.name}
              className="flex items-center justify-between px-4 py-3.5"
              style={{ borderBottom: i < 7 ? "0.5px solid rgba(255,255,255,0.04)" : "none" }}
            >
              <div>
                <div className="text-[14px] font-medium">{sec.name}</div>
                <div className="text-[11px] text-[#636366] mt-0.5">{sec.leader} {sec.leader_change >= 0 ? "+" : ""}{sec.leader_change}%</div>
              </div>
              <div className="text-[14px] font-semibold tabular-nums" style={{ color: sec.change_pct >= 0 ? "#30D158" : "#FF453A" }}>
                {sec.change_pct >= 0 ? "+" : ""}{sec.change_pct.toFixed(2)}%
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Top Movers */}
      <section>
        <div className="section-label">涨跌榜</div>
        <div className="grid grid-cols-2 gap-2.5">
          <div className="glass-card p-3.5">
            <div className="text-[11px] font-semibold mb-3" style={{ color: "#30D158" }}>涨幅 Top 5</div>
            {data.top_gainers.map((s) => (
              <div key={s.symbol} className="flex items-center justify-between py-1.5 text-[12px]" style={{ borderBottom: "0.5px solid rgba(255,255,255,0.03)" }}>
                <span className="truncate flex-1 text-[#C7C7CC]">{s.name}</span>
                <span className="font-semibold tabular-nums ml-2" style={{ color: "#30D158" }}>+{s.change_pct?.toFixed(2)}%</span>
              </div>
            ))}
          </div>
          <div className="glass-card p-3.5">
            <div className="text-[11px] font-semibold mb-3" style={{ color: "#FF453A" }}>跌幅 Top 5</div>
            {data.top_losers.map((s) => (
              <div key={s.symbol} className="flex items-center justify-between py-1.5 text-[12px]" style={{ borderBottom: "0.5px solid rgba(255,255,255,0.03)" }}>
                <span className="truncate flex-1 text-[#C7C7CC]">{s.name}</span>
                <span className="font-semibold tabular-nums ml-2" style={{ color: "#FF453A" }}>{s.change_pct?.toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </motion.div>
  );
}
