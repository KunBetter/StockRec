import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fetchDataFreshness, type DataFreshness } from "../../services/api";

export default function Header() {
  const [freshness, setFreshness] = useState<DataFreshness | null>(null);

  useEffect(() => {
    fetchDataFreshness().then(setFreshness).catch(() => {});
    const t = setInterval(() => fetchDataFreshness().then(setFreshness).catch(() => {}), 60000);
    return () => clearInterval(t);
  }, []);

  const isLive = freshness?.is_realtime;
  const updateTime = freshness?.latest_update
    ? new Date(freshness.latest_update).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <motion.header
      className="px-5 pt-3 pb-2"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2.5">
          <h1 className="m-0 text-[28px] font-bold tracking-[-0.40px]"
            style={{ fontFamily: '"SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif' }}>
            鲸灵宝
          </h1>
          <span className="px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide"
            style={{
              background: "linear-gradient(135deg, rgba(10,132,255,0.20), rgba(94,92,230,0.20))",
              color: "var(--blue)", border: "0.5px solid rgba(10,132,255,0.25)",
            }}>
            AI
          </span>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-full text-[12px] font-medium"
          style={{
            background: isLive ? "rgba(48,209,88,0.12)" : "rgba(255,159,10,0.12)",
            color: isLive ? "var(--green)" : "var(--orange)",
          }}>
          <span className={`w-1.5 h-1.5 rounded-full ${isLive ? "bg-[#30D158] animate-pulse" : "bg-[#FF9F0A]"}`} />
          {isLive && updateTime ? `实时 · ${updateTime}` : updateTime ? `收盘 · ${updateTime}` : "等待数据"}
        </div>
      </div>
      <p className="m-0 mt-1 text-[13px] text-[#98989D]">AI深度选股 · 如鲸探宝</p>
    </motion.header>
  );
}
