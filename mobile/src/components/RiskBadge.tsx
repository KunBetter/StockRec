import React from "react";
import { View, Text, StyleSheet } from "react-native";

const RISK_CONFIG: Record<string, { label: string; color: string }> = {
  low: { label: "低风险", color: "#34d399" },
  medium: { label: "中风险", color: "#fbbf24" },
  high: { label: "高风险", color: "#ef4444" },
};

export default function RiskBadge({ level }: { level: string | null }) {
  const config = RISK_CONFIG[level ?? ""] ?? { label: "未知", color: "#666" };
  return (
    <View style={[styles.badge, { backgroundColor: config.color + "20" }]}>
      <Text style={[styles.text, { color: config.color }]}>{config.label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  text: { fontSize: 11, fontWeight: "600" },
});
