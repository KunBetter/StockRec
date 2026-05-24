import { motion } from "framer-motion";

interface TabBarProps {
  active: string;
  onChange: (tab: string) => void;
}

const tabs = [
  {
    key: "recommend",
    label: "推荐",
    icon: "M11 2L14.09 8.26L21 9.27L16 14.14L17.18 21.02L11 17.77L4.82 21.02L6 14.14L1 9.27L7.91 8.26L11 2Z",
  },
  {
    key: "market",
    label: "行情",
    icon: "M1 3.5A2.5 2.5 0 013.5 1h2A2.5 2.5 0 018 3.5v2A2.5 2.5 0 015.5 8h-2A2.5 2.5 0 011 5.5v-2zM14 3.5A2.5 2.5 0 0116.5 1h2A2.5 2.5 0 0121 3.5v15A2.5 2.5 0 0118.5 21h-2A2.5 2.5 0 0114 18.5v-15zM1 14.5A2.5 2.5 0 013.5 12h2A2.5 2.5 0 018 14.5v4A2.5 2.5 0 015.5 21h-2A2.5 2.5 0 011 18.5v-4z",
  },
  {
    key: "profile",
    label: "我的",
    icon: "M11 3a4 4 0 100 8 4 4 0 000-8zM3 21a8 8 0 0116 0",
  },
];

export default function TabBar({ active, onChange }: TabBarProps) {
  return (
    <nav
      className="sticky bottom-0 z-50 mt-auto"
      style={{ paddingBottom: "var(--safe-bottom, 0px)" }}
    >
      <div
        className="flex justify-around py-1.5 px-2"
        style={{
          background: "rgba(28,28,30,0.86)",
          backdropFilter: "blur(24px) saturate(180%)",
          WebkitBackdropFilter: "blur(24px) saturate(180%)",
          borderTop: "0.5px solid rgba(255,255,255,0.08)",
        }}
      >
        {tabs.map((t) => {
          const isActive = active === t.key;
          return (
            <button
              key={t.key}
              onClick={() => onChange(t.key)}
              className="relative flex flex-col items-center gap-0.5 px-6 py-1 cursor-pointer"
              style={{ WebkitTapHighlightColor: "transparent" }}
            >
              {isActive && (
                <div className="absolute -top-0.5 left-1/2 -translate-x-1/2 w-4 h-0.5 rounded-full bg-[#0A84FF]" />
              )}
              <motion.svg
                width="22" height="22" viewBox="0 0 22 22"
                fill={isActive ? "#0A84FF" : "#636366"}
                animate={{ scale: isActive ? 1.05 : 0.92 }}
                transition={{ type: "spring", stiffness: 400, damping: 25 }}
              >
                <path d={t.icon} />
              </motion.svg>
              <motion.span
                className="text-[10px] font-medium"
                animate={{ color: isActive ? "#FFFFFF" : "#636366" }}
                transition={{ duration: 0.2 }}
              >
                {t.label}
              </motion.span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
