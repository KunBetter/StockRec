interface ErrorStateProps { message: string; onRetry: () => void; }

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 px-5">
      <div className="w-14 h-14 rounded-full flex items-center justify-center mb-5" style={{ background: "rgba(255,69,58,0.12)" }}>
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <circle cx="11" cy="11" r="9" stroke="#FF453A" strokeWidth="1.5"/>
          <path d="M11 7v5M11 15v1" stroke="#FF453A" strokeWidth="1.8" strokeLinecap="round"/>
        </svg>
      </div>
      <p className="text-[14px] text-[#98989D] mb-5 text-center">{message}</p>
      <button
        onClick={onRetry}
        className="px-6 py-2.5 rounded-full text-[14px] font-semibold text-white bg-[#0A84FF] spring-press"
      >
        重试
      </button>
    </div>
  );
}
