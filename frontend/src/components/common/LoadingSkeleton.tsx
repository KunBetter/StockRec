export default function LoadingSkeleton() {
  return (
    <div className="px-5 py-4 space-y-3">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-2xl p-4 animate-pulse"
          style={{ background: "rgba(255,255,255,0.04)" }}
        >
          <div className="flex justify-between mb-3">
            <div className="space-y-2">
              <div className="h-5 w-20 rounded bg-[#2C2C2E]" />
              <div className="h-3 w-14 rounded bg-[#2C2C2E]" />
            </div>
            <div className="h-8 w-16 rounded bg-[#2C2C2E]" />
          </div>
          <div className="space-y-2">
            <div className="h-1.5 w-full rounded bg-[#2C2C2E]" />
            <div className="h-1.5 w-3/4 rounded bg-[#2C2C2E]" />
            <div className="h-1.5 w-1/2 rounded bg-[#2C2C2E]" />
          </div>
        </div>
      ))}
    </div>
  );
}
