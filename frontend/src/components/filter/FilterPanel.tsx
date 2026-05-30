import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface FilterPanelProps {
  open: boolean;
  onClose: () => void;
  onApply: (params: Record<string, string>) => void;
}

const PRESETS = [
  { key: "high_dividend", label: "高股息", desc: "股息率 > 3%" },
  { key: "low_pe", label: "低估值", desc: "PE < 15" },
  { key: "high_growth", label: "高成长", desc: "营收增速 > 20%" },
  { key: "high_roe", label: "高ROE", desc: "ROE > 15%" },
  { key: "low_volatility", label: "低波动", desc: "低beta" },
  { key: "breakout", label: "强势突破", desc: "突破60日高点" },
];

export default function FilterPanel({ open, onClose, onApply }: FilterPanelProps) {
  const [selectedRisks, setSelectedRisks] = useState<Set<string>>(new Set());
  const [selectedPresets, setSelectedPresets] = useState<Set<string>>(new Set());

  const toggleRisk = (r: string) => {
    const next = new Set(selectedRisks); next.has(r) ? next.delete(r) : next.add(r); setSelectedRisks(next);
  };
  const togglePreset = (p: string) => {
    const next = new Set(selectedPresets); next.has(p) ? next.delete(p) : next.add(p); setSelectedPresets(next);
  };

  const handleApply = () => {
    const params: Record<string, string> = {};
    if (selectedRisks.size > 0) params.risk_level = [...selectedRisks].join(",");
    onApply(params);
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div className="absolute inset-0 z-50" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          onClick={onClose} style={{ background: "rgba(0,0,0,0.6)" }}>
          <motion.div className="absolute bottom-0 left-0 right-0 rounded-t-[24px] p-5 pb-8"
            initial={{ y: "100%" }} animate={{ y: 0 }} exit={{ y: "100%" }} transition={{ type: "spring", damping: 25, stiffness: 300 }}
            onClick={(e) => e.stopPropagation()}
            style={{ background: "#1C1C1E" }}>
            <div className="w-8 h-1 rounded-full bg-[#636366] mx-auto mb-4" />

            <div className="text-[16px] font-bold mb-4">筛选</div>

            <div className="mb-5">
              <div className="text-[11px] font-semibold text-[#98989D] mb-2">风险等级</div>
              <div className="flex gap-2">
                {["low", "medium", "high"].map((r) => (
                  <button key={r} onClick={() => toggleRisk(r)} className="px-4 py-2 rounded-full text-[11px] font-medium"
                    style={{ background: selectedRisks.has(r) ? "#0A84FF" : "rgba(118,118,128,0.16)", color: selectedRisks.has(r) ? "#fff" : "#8E8E93" }}>
                    {{ low: "低风险", medium: "中风险", high: "高风险" }[r]}
                  </button>
                ))}
              </div>
            </div>

            <div className="mb-5">
              <div className="text-[11px] font-semibold text-[#98989D] mb-2">预置策略</div>
              <div className="flex flex-wrap gap-2">
                {PRESETS.map((p) => (
                  <button key={p.key} onClick={() => togglePreset(p.key)} className="px-3 py-1.5 rounded-full text-[10px]"
                    style={{ background: selectedPresets.has(p.key) ? "rgba(10,132,255,0.15)" : "rgba(255,255,255,0.05)", color: selectedPresets.has(p.key) ? "#0A84FF" : "#8E8E93", border: selectedPresets.has(p.key) ? "0.5px solid rgba(10,132,255,0.3)" : "none" }}>
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <button onClick={handleApply} className="w-full py-3 rounded-xl bg-[#0A84FF] text-white text-[14px] font-bold">
              应用筛选
            </button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
