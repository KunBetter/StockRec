import { motion } from "framer-motion";

export default function Header() {
  return (
    <motion.header
      className="px-5 pt-3 pb-2"
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.1, 0.25, 1] }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2.5">
          <h1
            className="m-0 text-[28px] font-bold tracking-[-0.40px]"
            style={{ fontFamily: '"SF Pro Display", -apple-system, BlinkMacSystemFont, sans-serif' }}
          >
            鲸灵宝
          </h1>
          <span
            className="px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide"
            style={{
              background: "linear-gradient(135deg, rgba(10,132,255,0.20), rgba(94,92,230,0.20))",
              color: "var(--blue)",
              border: "0.5px solid rgba(10,132,255,0.25)",
            }}
          >
            AI
          </span>
        </div>
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-full text-[12px] font-medium"
          style={{ background: "rgba(48,209,88,0.12)", color: "var(--green)" }}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-[#30D158] animate-pulse" />
          市场开放
        </div>
      </div>
      <p className="m-0 mt-1 text-[13px] text-[#98989D]">
        AI深度选股 · 如鲸探宝
      </p>
    </motion.header>
  );
}
