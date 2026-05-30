interface LayerBreakdownProps {
  layerScores: { layer1_factor: number | null; layer2_ml: number | null; layer3_event: number | null } | null;
}

const layers = [
  { key: "layer1_factor", label: "Layer 1 · 多因子模型", weight: "60%", color: "#0A84FF", tags: ["动量", "价值", "质量", "成长", "波动"] },
  { key: "layer2_ml", label: "Layer 2 · 机器学习预测", weight: "30%", color: "#5E5CE6", tags: ["LightGBM · 5年数据 · 128维特征"] },
  { key: "layer3_event", label: "Layer 3 · 事件驱动", weight: "10%", color: "#FF9F0A", tags: ["财报", "回购", "分红", "公告"] },
] as const;

export default function LayerBreakdown({ layerScores }: LayerBreakdownProps) {
  if (!layerScores) return null;

  return (
    <div className="glass-card p-4 mb-4">
      <div className="text-[12px] font-semibold text-[#C7C7CC] mb-3">三层评分引擎</div>
      {layers.map((l) => {
        const score = layerScores[l.key as keyof typeof layerScores] ?? 0;
        const pct = Math.min(100, Math.max(0, score));
        return (
          <div key={l.key} className="mb-3 last:mb-0">
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-semibold" style={{ color: l.color }}>{l.label}</span>
              <span className="text-[9px] text-[#8E8E93]">权重 {l.weight}</span>
            </div>
            <div className="h-1 rounded-full mb-2" style={{ background: "rgba(255,255,255,0.06)" }}>
              <div className="h-full rounded-full transition-all duration-600" style={{ width: `${pct}%`, background: l.color }} />
            </div>
            <div className="flex flex-wrap gap-1.5">
              {l.tags.map((t) => (
                <span key={t} className="px-2 py-0.5 rounded-md text-[8px]" style={{ background: `${l.color}14`, color: l.color }}>
                  {t}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
