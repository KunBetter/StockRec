import React from "react";
import { View, Text, TouchableOpacity, StyleSheet } from "react-native";
import type { StockRecommendation } from "../types/stock";
import ScoreBar from "./ScoreBar";
import RiskBadge from "./RiskBadge";

interface Props {
  stock: StockRecommendation;
  onPress: () => void;
}

export default function StockCard({ stock, onPress }: Props) {
  const priceColor =
    (stock.price_change_pct ?? 0) >= 0 ? "#34d399" : "#ef4444";
  const changeStr =
    stock.price_change_pct != null
      ? `${stock.price_change_pct >= 0 ? "+" : ""}${stock.price_change_pct.toFixed(2)}%`
      : "--";

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.topRow}>
        <View style={styles.nameRow}>
          <Text style={styles.name}>{stock.name}</Text>
          <RiskBadge level={stock.risk_level} />
        </View>
        <Text style={styles.score}>{stock.composite_score?.toFixed(1) ?? "--"}</Text>
      </View>

      <View style={styles.midRow}>
        <Text style={styles.symbol}>{stock.symbol}</Text>
        <View style={styles.priceRow}>
          <Text style={styles.price}>
            ¥{stock.current_price?.toFixed(2) ?? "--"}
          </Text>
          <Text style={[styles.change, { color: priceColor }]}>{changeStr}</Text>
        </View>
      </View>

      <View style={styles.bars}>
        <ScoreBar label="预期收益" value={stock.predicted_return} color="#34d399" />
        <ScoreBar label="动量" value={stock.momentum_score} color="#60a5fa" />
        <ScoreBar label="质量" value={stock.quality_score} color="#fbbf24" />
      </View>

      {stock.ai_summary ? (
        <Text style={styles.summary} numberOfLines={2}>
          {stock.ai_summary}
        </Text>
      ) : null}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: "#111",
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
    borderLeftWidth: 3,
    borderLeftColor: "#34d399",
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  name: { fontSize: 17, fontWeight: "600", color: "#fff" },
  score: {
    fontSize: 22,
    fontWeight: "700",
    color: "#34d399",
    fontVariant: ["tabular-nums"],
  },
  midRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  symbol: { fontSize: 13, color: "#666" },
  priceRow: { flexDirection: "row", alignItems: "baseline", gap: 8 },
  price: { fontSize: 16, color: "#fff", fontWeight: "500" },
  change: { fontSize: 14, fontWeight: "500" },
  bars: { gap: 4, marginBottom: 8 },
  summary: { fontSize: 12, color: "#888", lineHeight: 18 },
});
