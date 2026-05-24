export default function ScoreBar({ score, label }: { score: number; label: string }) {
  const pct = Math.min(100, Math.max(0, score));
  const color = pct >= 70 ? "#30D158" : pct >= 40 ? "#FF9F0A" : "#FF453A";

  return (
    <div className="flex items-center gap-2">
      <span className="text-[11px] w-6 text-right text-[#8E8E93] font-medium">{label}</span>
      <div className="flex-1 h-1 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
        <div
          className="h-full rounded-full transition-all duration-600 ease-out"
          style={{ width: `${pct}%`, background: color, boxShadow: `0 0 6px ${color}40` }}
        />
      </div>
      <span className="text-[11px] font-semibold tabular-nums w-7" style={{ color }}>{score.toFixed(0)}</span>
    </div>
  );
}
