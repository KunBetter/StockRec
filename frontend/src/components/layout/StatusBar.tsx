import { useEffect, useState } from "react";

export default function StatusBar() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const h = now.getHours().toString().padStart(2, "0");
      const m = now.getMinutes().toString().padStart(2, "0");
      setTime(`${h}:${m}`);
    };
    update();
    const id = setInterval(update, 10000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="phone-status-bar">
      <span className="text-[14px] font-semibold tracking-tight" style={{ width: 54 }}>{time}</span>
      <div className="flex items-center gap-1.5">
        <svg width="16" height="11" viewBox="0 0 16 11" fill="none">
          <rect x="0" y="6" width="2.5" height="5" rx="0.6" fill="white"/>
          <rect x="3.5" y="4" width="2.5" height="7" rx="0.6" fill="white"/>
          <rect x="7" y="2" width="2.5" height="9" rx="0.6" fill="white"/>
          <rect x="10.5" y="0" width="2.5" height="11" rx="0.6" fill="white"/>
        </svg>
        <svg width="27" height="12" viewBox="0 0 27 12" fill="none">
          <rect x="0.5" y="0.5" width="22" height="11" rx="2.5" stroke="white" strokeOpacity="0.35" strokeWidth="1"/>
          <rect x="2" y="2" width="18" height="8" rx="1.5" fill="white"/>
          <path d="M24 3.5v5a2 2 0 002 2v-9a2 2 0 00-2 2z" fill="white" fillOpacity="0.4"/>
        </svg>
      </div>
    </div>
  );
}
