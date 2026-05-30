import { motion } from "framer-motion";

interface QuickActionsProps {
  onAIChat: () => void;
  onAnalysis: () => void;
}

export default function QuickActions({ onAIChat, onAnalysis }: QuickActionsProps) {
  return (
    <div className="flex gap-2.5 px-4 mt-3 mb-2">
      <motion.button
        onClick={onAIChat}
        className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl text-left"
        style={{ background: "rgba(10,132,255,0.08)", border: "0.5px solid rgba(10,132,255,0.12)" }}
        whileTap={{ scale: 0.96 }}
      >
        <span className="text-[18px]">💬</span>
        <div>
          <div className="text-[11px] font-semibold text-[#0A84FF]">AI 选股问答</div>
          <div className="text-[9px] text-[#636366]">问任何股票相关问题</div>
        </div>
      </motion.button>
      <motion.button
        onClick={onAnalysis}
        className="flex-1 flex items-center gap-3 px-4 py-3 rounded-xl text-left"
        style={{ background: "rgba(94,92,230,0.08)", border: "0.5px solid rgba(94,92,230,0.12)" }}
        whileTap={{ scale: 0.96 }}
      >
        <span className="text-[18px]">🔍</span>
        <div>
          <div className="text-[11px] font-semibold text-[#5E5CE6]">深度分析</div>
          <div className="text-[9px] text-[#636366]">财务+财报+行业</div>
        </div>
      </motion.button>
    </div>
  );
}
