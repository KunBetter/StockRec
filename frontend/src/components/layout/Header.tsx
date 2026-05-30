import { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { fetchDataFreshness, type DataFreshness } from "../../services/api";

function getStatusLabel(freshness: DataFreshness | null, loading: boolean): { dotClass: string; text: string; bgColor: string; textColor: string } {
  if (loading) {
    return {
      dotClass: "w-1.5 h-1.5 rounded-full bg-[#636366]",
      text: "加载中...",
      bgColor: "rgba(118,118,128,0.12)",
      textColor: "#8E8E93",
    };
  }
  if (!freshness) {
    return {
      dotClass: "w-1.5 h-1.5 rounded-full bg-[#636366]",
      text: "无数据",
      bgColor: "rgba(118,118,128,0.12)",
      textColor: "#8E8E93",
    };
  }
  const updateTime = freshness.latest_update
    ? new Date(freshness.latest_update).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
    : null;
  if (freshness.is_realtime && updateTime) {
    return {
      dotClass: "w-1.5 h-1.5 rounded-full bg-[#30D158] animate-pulse",
      text: `实时 · ${updateTime}`,
      bgColor: "rgba(48,209,88,0.12)",
      textColor: "var(--green)",
    };
  }
  if (updateTime) {
    return {
      dotClass: "w-1.5 h-1.5 rounded-full bg-[#FF9F0A]",
      text: `收盘 · ${updateTime}`,
      bgColor: "rgba(255,159,10,0.12)",
      textColor: "var(--orange)",
    };
  }
  return {
    dotClass: "w-1.5 h-1.5 rounded-full bg-[#636366]",
    text: "等待数据",
    bgColor: "rgba(118,118,128,0.12)",
    textColor: "#8E8E93",
  };
}

export default function Header() {
  const [freshness, setFreshness] = useState<DataFreshness | null>(null);
  const [loading, setLoading] = useState(true);
  const mountedRef = useRef(true);

  const load = useCallback(async () => {
    try {
      const data = await fetchDataFreshness();
      if (mountedRef.current) {
        setFreshness(data);
        setLoading(false);
      }
    } catch {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    load();
    const t = setInterval(load, 60000);
    return () => {
      mountedRef.current = false;
      clearInterval(t);
    };
  }, [load]);

  const status = getStatusLabel(freshness, loading);

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
          style={{ background: status.bgColor, color: status.textColor }}>
          <span className={status.dotClass} />
          {status.text}
        </div>
      </div>
      <p className="m-0 mt-1 text-[13px] text-[#98989D]">AI深度选股 · 如鲸探宝</p>
    </motion.header>
  );
}
