interface AIAnalysisProps {
  recommendation: string | null;
  risk_flags: string[];
}

export default function AIAnalysis({ recommendation, risk_flags }: AIAnalysisProps) {
  if (!recommendation && risk_flags.length === 0) return null;

  return (
    <div className="glass-card p-4 mb-4" style={{ border: "0.5px solid rgba(10,132,255,0.10)" }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[13px]">🤖</span>
        <span className="text-[12px] font-semibold text-[#C7C7CC]">AI 深度分析</span>
        <span className="ml-auto text-[8px] text-[#636366]">Powered by DeepSeek</span>
      </div>
      {recommendation && (
        <p className="text-[11px] leading-relaxed m-0 mb-3 text-[#98989D]">{recommendation}</p>
      )}
      {risk_flags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {risk_flags.map((f, i) => (
            <span key={i} className="px-2 py-1 rounded-md text-[9px]" style={{ background: "rgba(255,69,58,0.08)", color: "#FF453A" }}>
              ⚠ {f}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
