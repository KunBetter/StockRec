const riskColors: Record<string, { bg: string; text: string; label: string }> = {
  low: { bg: "rgba(48,209,88,0.15)", text: "#30D158", label: "低风险" },
  medium: { bg: "rgba(255,159,10,0.15)", text: "#FF9F0A", label: "中风险" },
  high: { bg: "rgba(255,69,58,0.15)", text: "#FF453A", label: "高风险" },
};

export default function RiskBadge({ level }: { level: string }) {
  const c = riskColors[level] || riskColors.medium;
  return (
    <span
      className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-bold tracking-wide"
      style={{ background: c.bg, color: c.text }}
    >
      {c.label}
    </span>
  );
}
