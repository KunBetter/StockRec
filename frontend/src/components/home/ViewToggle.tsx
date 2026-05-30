import { motion } from "framer-motion";

interface ViewToggleProps {
  view: "featured" | "list";
  onChange: (v: "featured" | "list") => void;
  total: number;
}

export default function ViewToggle({ view, onChange, total }: ViewToggleProps) {
  return (
    <div className="flex items-center gap-3 px-4 mb-3">
      <div className="flex rounded-lg p-0.5" style={{ background: "rgba(118,118,128,0.16)" }}>
        {(["featured", "list"] as const).map((v) => (
          <motion.button
            key={v}
            onClick={() => onChange(v)}
            className="relative px-4 py-1.5 rounded-[7px] text-[11px] font-semibold"
            whileTap={{ scale: 0.95 }}
            animate={{ color: view === v ? "#FFFFFF" : "#8E8E93" }}
          >
            {view === v && (
              <motion.div className="absolute inset-0 rounded-[7px] bg-[#0A84FF]"
                layoutId="viewToggle" transition={{ type: "spring", stiffness: 400, damping: 30 }} />
            )}
            <span className="relative z-10">{v === "featured" ? "精选" : "列表"}</span>
          </motion.button>
        ))}
      </div>
      <span className="text-[11px] text-[#636366]">{total}只</span>
    </div>
  );
}
