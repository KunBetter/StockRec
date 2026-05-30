import { useState, useEffect } from "react";
import { fetchPeers } from "../../services/api";
import type { PeerStock } from "../../types/stock";

interface PeerComparisonProps { symbol: string; }

export default function PeerComparison({ symbol }: PeerComparisonProps) {
  const [peers, setPeers] = useState<PeerStock[]>([]);

  useEffect(() => {
    fetchPeers(symbol).then(d => setPeers(d.peers || [])).catch(() => {});
  }, [symbol]);

  if (peers.length === 0) return null;

  return (
    <div className="glass-card p-4 mb-4">
      <div className="text-[12px] font-semibold text-[#C7C7CC] mb-3">同行业对比</div>
      <div className="flex text-[9px] text-[#636366] px-2 mb-1">
        <span className="flex-1">名称</span><span className="w-10 text-center">评分</span><span className="w-10 text-right">PE</span><span className="w-10 text-right">ROE</span>
      </div>
      {peers.map((p) => (
        <div key={p.symbol} className="flex items-center px-2 py-1.5 rounded-md text-[10px]"
          style={{ background: p.symbol === symbol ? "rgba(48,209,88,0.06)" : "transparent" }}>
          <span className="flex-1 font-medium" style={{ color: p.symbol === symbol ? "#30D158" : "#8E8E93" }}>{p.name}</span>
          <span className="w-10 text-center font-semibold" style={{ color: (p.composite_score ?? 0) >= 70 ? "#30D158" : "#8E8E93" }}>{p.composite_score?.toFixed(0) ?? "-"}</span>
          <span className="w-10 text-right text-[#8E8E93]">{p.pe ?? "-"}</span>
          <span className="w-10 text-right text-[#8E8E93]">{p.roe?.toFixed(1) ?? "-"}%</span>
        </div>
      ))}
    </div>
  );
}
