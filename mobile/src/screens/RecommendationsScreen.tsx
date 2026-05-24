import React, { useState, useEffect, useCallback } from "react";
import {
  View, Text, FlatList, TouchableOpacity,
  StyleSheet, RefreshControl,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { fetchRecommendations } from "../services/api";
import StockCard from "../components/StockCard";
import LoadingSkeleton from "../components/LoadingSkeleton";
import type { RecommendationsResponse, RiskSection } from "../types/stock";

const RISK_TABS: { key: string; label: string; color: string }[] = [
  { key: "low", label: "低风险", color: "#34d399" },
  { key: "medium", label: "中风险", color: "#fbbf24" },
  { key: "high", label: "高风险", color: "#ef4444" },
];

export default function RecommendationsScreen() {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("low");
  const navigation = useNavigation<any>();

  const load = useCallback(async () => {
    try {
      const res = await fetchRecommendations();
      setData(res);
    } catch (e) {
      console.error("Failed to load recommendations:", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    load();
  };

  if (loading) return <LoadingSkeleton />;

  const activeSection: RiskSection | undefined = data?.sections?.find(
    (s) => s.risk_level === activeTab,
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>鲸灵宝 AI</Text>
        <Text style={styles.subtitle}>
          {data?.date ?? "---"} · 更新于 {data?.generated_at?.slice(11, 16) ?? "--:--"}
        </Text>
      </View>

      {/* Risk tabs */}
      <View style={styles.tabs}>
        {RISK_TABS.map((tab) => (
          <TouchableOpacity
            key={tab.key}
            style={[
              styles.tab,
              activeTab === tab.key && { backgroundColor: tab.color + "20" },
            ]}
            onPress={() => setActiveTab(tab.key)}
          >
            <Text
              style={[
                styles.tabText,
                activeTab === tab.key && { color: tab.color },
              ]}
            >
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        data={activeSection?.stocks ?? []}
        keyExtractor={(item) => item.symbol}
        renderItem={({ item }) => (
          <StockCard
            stock={item}
            onPress={() => navigation.navigate("StockDetail", { symbol: item.symbol })}
          />
        )}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#34d399" />
        }
        ListEmptyComponent={
          <Text style={styles.empty}>暂无推荐数据</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  header: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 12 },
  title: { fontSize: 28, fontWeight: "700", color: "#fff" },
  subtitle: { fontSize: 13, color: "#888", marginTop: 4 },
  tabs: {
    flexDirection: "row",
    paddingHorizontal: 20,
    gap: 10,
    marginBottom: 12,
  },
  tab: {
    paddingHorizontal: 18,
    paddingVertical: 8,
    borderRadius: 16,
    backgroundColor: "#1a1a1a",
  },
  tabText: { fontSize: 14, color: "#888" },
  list: { paddingHorizontal: 20, paddingBottom: 100 },
  empty: { color: "#666", textAlign: "center", marginTop: 40, fontSize: 14 },
});
