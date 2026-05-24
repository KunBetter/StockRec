export default function AIAnalysisPreview({ summary }: { summary: string | null }) {
  if (!summary) {
    return (
      <p className="text-[11px] italic m-0 text-[#636366]">AI 分析进行中...</p>
    );
  }
  return (
    <p className="text-[11px] leading-relaxed m-0 line-clamp-2 text-[#8E8E93]">
      {summary}
    </p>
  );
}
