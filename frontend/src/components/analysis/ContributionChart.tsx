import type { ScoreBreakdown } from "../../types/stock";

const labelMap: Record<string, string> = {
  predicted_return: "预期收益", momentum_score: "动量趋势",
  quality_score: "基本面质量", sentiment_score: "AI情绪",
};

export default function ContributionChart({ breakdown, total }: { breakdown: ScoreBreakdown | null; total: number }) {
  if (!breakdown) return null;
  const entries = Object.entries(breakdown).filter(([, v]) => v.value > 0);

  return (
    <div className="glass-card p-4 mb-4">
      <div className="text-[12px] font-semibold text-[#C7C7CC] mb-3">分数构成 · 贡献拆解</div>
      <div className="flex items-end gap-2 h-16 mb-3">
        {entries.map(([key, item]) => {
          const h = Math.max(4, (item.contribution / Math.max(total, 1)) * 100);
          return (
            <div key={key} className="flex-1 text-center">
              <div className="rounded-t-sm mx-auto" style={{
                height: `${Math.max(4, h)}%`,
                minHeight: 4,
                background: `linear-gradient(180deg, #0A84FF, rgba(10,132,255,0.3))`,
                width: "70%",
              }} />
              <div className="text-[7px] text-[#636366] mt-1">{labelMap[key] || key}</div>
            </div>
          );
        })}
      </div>
      {entries.map(([key, item]) => (
        <div key={key} className="flex justify-between text-[10px] py-1" style={{ borderBottom: "0.5px solid rgba(255,255,255,0.04)" }}>
          <span className="text-[#98989D]">{labelMap[key] || key} <span className="text-[#636366]">({(item.weight * 100).toFixed(0)}%)</span></span>
          <span className="font-semibold text-[#C7C7CC]">{item.contribution.toFixed(1)}</span>
        </div>
      ))}
      <div className="text-right text-[11px] font-bold text-[#30D158] mt-2">= {total.toFixed(1)}</div>
    </div>
  );
}
