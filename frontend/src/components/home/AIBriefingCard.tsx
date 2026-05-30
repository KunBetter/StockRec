import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { fetchBriefing, type BriefingResponse } from "../../services/api";

export default function AIBriefingCard() {
  const [data, setData] = useState<BriefingResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBriefing()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading || !data) return null;

  return (
    <motion.div
      className="mx-4 mb-3 rounded-[14px] p-3"
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        background: "linear-gradient(135deg, rgba(10,132,255,0.06), rgba(94,92,230,0.04))",
        border: "0.5px solid rgba(10,132,255,0.12)",
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[14px]">🤖</span>
        <span className="text-[12px] font-semibold text-[#C7C7CC]">今日AI市场简报</span>
        <span className="ml-auto text-[9px] text-[#636366]">
          {new Date(data.generated_at).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })} 更新
        </span>
      </div>
      <p className="text-[11px] leading-relaxed m-0 text-[#98989D] line-clamp-3">{data.summary}</p>
      {data.highlights && data.highlights.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {data.highlights.map((h, i) => (
            <span key={i} className="text-[9px] px-2 py-0.5 rounded-full"
              style={{ background: "rgba(10,132,255,0.1)", color: "#0A84FF" }}>
              {h}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
