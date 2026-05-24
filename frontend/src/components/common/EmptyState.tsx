export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-5">
      <div className="w-14 h-14 rounded-full flex items-center justify-center mb-5" style={{ background: "rgba(10,132,255,0.10)" }}>
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <rect x="1" y="1" width="20" height="20" rx="4" stroke="#0A84FF" strokeWidth="1.2"/>
          <path d="M7 11h8M11 7v8" stroke="#0A84FF" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </div>
      <p className="text-[16px] font-semibold mb-1.5">暂无推荐数据</p>
      <p className="text-[13px] text-[#98989D] text-center">系统正在分析市场数据，请稍后再来</p>
    </div>
  );
}
