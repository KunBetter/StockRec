import React from "react";
import { View, Text, StyleSheet } from "react-native";

interface Props {
  label: string;
  value: number | null;
  color: string;
}

export default function ScoreBar({ label, value, color }: Props) {
  const pct = Math.min(Math.max((value ?? 0) / 100, 0), 1);

  return (
    <View style={styles.row}>
      <Text style={styles.label}>{label}</Text>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${pct * 100}%`, backgroundColor: color }]} />
      </View>
      <Text style={[styles.value, { color }]}>{value?.toFixed(0) ?? "--"}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 8 },
  label: { fontSize: 11, color: "#888", width: 52 },
  track: {
    flex: 1,
    height: 4,
    backgroundColor: "#222",
    borderRadius: 2,
    overflow: "hidden",
  },
  fill: { height: "100%", borderRadius: 2 },
  value: { fontSize: 11, fontWeight: "600", width: 28, textAlign: "right" },
});
