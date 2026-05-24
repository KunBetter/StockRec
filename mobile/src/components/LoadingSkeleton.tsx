import React from "react";
import { View, StyleSheet } from "react-native";

export default function LoadingSkeleton() {
  return (
    <View style={styles.container}>
      {[1, 2, 3, 4, 5].map((i) => (
        <View key={i} style={styles.card}>
          <View style={styles.row}>
            <View style={[styles.bar, { width: 120, height: 18 }]} />
            <View style={[styles.bar, { width: 50, height: 24 }]} />
          </View>
          <View style={[styles.bar, { width: 80, height: 14, marginTop: 8 }]} />
          <View style={[styles.bar, { width: "100%", height: 4, marginTop: 12 }]} />
          <View style={[styles.bar, { width: "80%", height: 4, marginTop: 6 }]} />
          <View style={[styles.bar, { width: "60%", height: 4, marginTop: 6 }]} />
          <View style={[styles.bar, { width: "90%", height: 12, marginTop: 10 }]} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000", padding: 20, paddingTop: 60 },
  card: {
    backgroundColor: "#111",
    borderRadius: 14,
    padding: 16,
    marginBottom: 10,
  },
  row: { flexDirection: "row", justifyContent: "space-between" },
  bar: { backgroundColor: "#1a1a1a", borderRadius: 4 },
});
