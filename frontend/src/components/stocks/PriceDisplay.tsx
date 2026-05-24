export default function PriceDisplay({ price, change }: { price: number | null; change: number | null }) {
  const c = change ?? 0;
  const isUp = c >= 0;
  const color = c === 0 ? "#98989D" : isUp ? "#30D158" : "#FF453A";

  return (
    <span className="text-[12px] font-semibold tabular-nums" style={{ color }}>
      {isUp && c !== 0 ? "+" : ""}{c.toFixed(2)}%
    </span>
  );
}
