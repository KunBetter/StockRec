import React, { useState, useEffect, useCallback } from "react";
import {
  View, Text, ScrollView, StyleSheet, RefreshControl,
} from "react-native";
import { fetchMarketOverview } from "../services/api";
import LoadingSkeleton from "../components/LoadingSkeleton";
import type { MarketOverviewResponse } from "../types/stock";

export default function MarketScreen() {
  const [data, setData] = useState<MarketOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const res = await fetchMarketOverview();
      setData(res);
    } catch (e) {
      console.error("Failed to load market:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <LoadingSkeleton />;

  const index = data?.indices?.[0];
  const breadth = data?.breadth;

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor="#34d399" />
      }
    >
      <View style={styles.header}>
        <Text style={styles.title}>行情</Text>
      </View>

      {/* Main index */}
      {index && (
        <View style={styles.indexCard}>
          <Text style={styles.indexName}>{index.name}</Text>
          <Text style={styles.indexValue}>
            {index.value?.toLocaleString() ?? "--"}
          </Text>
          <Text
            style={[
              styles.indexChange,
              { color: (index.change_pct ?? 0) >= 0 ? "#34d399" : "#ef4444" },
            ]}
          >
            {(index.change_pct ?? 0) >= 0 ? "+" : ""}
            {index.change_pct?.toFixed(2) ?? "--"}%
          </Text>
        </View>
      )}

      {/* Breadth */}
      {breadth && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>涨跌分布</Text>
          <View style={styles.breadthBar}>
            <View
              style={[
                styles.breadthDown,
                { flex: breadth.down || 1 },
              ]}
            />
            <View
              style={[
                styles.breadthFlat,
                { flex: breadth.flat || 1 },
              ]}
            />
            <View
              style={[
                styles.breadthUp,
                { flex: breadth.up || 1 },
              ]}
            />
          </View>
          <View style={styles.breadthLabels}>
            <Text style={styles.redText}>跌 {breadth.down} 家</Text>
            <Text style={styles.grayText}>平 {breadth.flat} 家</Text>
            <Text style={styles.greenText}>涨 {breadth.up} 家</Text>
          </View>
        </View>
      )}

      {/* Sectors */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>板块排行</Text>
        {(data?.sectors ?? []).slice(0, 8).map((s) => (
          <View key={s.name} style={styles.row}>
            <Text style={styles.rowName}>{s.name}</Text>
            <Text
              style={[
                styles.rowValue,
                { color: s.change_pct >= 0 ? "#34d399" : "#ef4444" },
              ]}
            >
              {s.change_pct >= 0 ? "+" : ""}{s.change_pct.toFixed(2)}%
            </Text>
          </View>
        ))}
      </View>

      {/* Top movers */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>涨幅榜</Text>
        {(data?.top_gainers ?? []).slice(0, 5).map((s) => (
          <View key={s.symbol} style={styles.row}>
            <Text style={styles.rowName}>{s.name}</Text>
            <Text style={[styles.rowValue, { color: "#34d399" }]}>
              +{s.change_pct.toFixed(2)}%
            </Text>
          </View>
        ))}
      </View>

      <View style={{ height: 100 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  header: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 12 },
  title: { fontSize: 28, fontWeight: "700", color: "#fff" },
  indexCard: {
    margin: 20,
    backgroundColor: "#111",
    borderRadius: 16,
    padding: 24,
    alignItems: "center",
  },
  indexName: { fontSize: 16, color: "#888" },
  indexValue: { fontSize: 36, fontWeight: "700", color: "#fff", marginTop: 8 },
  indexChange: { fontSize: 18, fontWeight: "600", marginTop: 4 },
  section: { paddingHorizontal: 20, marginTop: 24 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#fff", marginBottom: 12 },
  breadthBar: { flexDirection: "row", height: 8, borderRadius: 4, overflow: "hidden" },
  breadthDown: { backgroundColor: "#ef4444" },
  breadthFlat: { backgroundColor: "#333" },
  breadthUp: { backgroundColor: "#34d399" },
  breadthLabels: { flexDirection: "row", justifyContent: "space-between", marginTop: 8 },
  redText: { color: "#ef4444", fontSize: 12 },
  grayText: { color: "#666", fontSize: 12 },
  greenText: { color: "#34d399", fontSize: 12 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#222",
  },
  rowName: { fontSize: 14, color: "#ccc" },
  rowValue: { fontSize: 14, fontWeight: "600" },
});
