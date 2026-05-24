import { motion } from "framer-motion";

interface Range { label: string; min: number | null; max: number | null; }

const RANGES: Range[] = [
  { label: "全部", min: null, max: null },
  { label: "<10", min: null, max: 10 },
  { label: "10-30", min: 10, max: 30 },
  { label: "30-100", min: 30, max: 100 },
  { label: ">100", min: 100, max: null },
];

interface Props { selected: number; onChange: (i: number) => void; }

export default function PriceRangeSelector({ selected, onChange }: Props) {
  return (
    <div className="flex gap-2 px-5 pt-3 pb-2 overflow-visible">
      {RANGES.map((r, i) => (
        <motion.button
          key={r.label}
          onClick={() => onChange(i)}
          className="relative px-4 py-2 rounded-full text-[13px] font-semibold whitespace-nowrap"
          whileTap={{ scale: 0.94 }}
          animate={{
            background: selected === i ? "var(--blue)" : "rgba(118,118,128,0.14)",
            color: selected === i ? "#FFFFFF" : "#98989D",
          }}
          transition={{ duration: 0.2 }}
        >
          {r.label}
        </motion.button>
      ))}
    </div>
  );
}

export { RANGES };
export type { Range };
