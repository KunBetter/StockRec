import React, { useState, useEffect } from "react";
import {
  View, Text, ScrollView, StyleSheet, TouchableOpacity,
} from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import { fetchStockAnalysis } from "../services/api";
import RiskBadge from "../components/RiskBadge";
import ScoreBar from "../components/ScoreBar";
import LoadingSkeleton from "../components/LoadingSkeleton";
import type { AnalysisDetail } from "../types/stock";

export default function StockDetailScreen() {
  const route = useRoute<any>();
  const navigation = useNavigation();
  const { symbol } = route.params;
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetchStockAnalysis(symbol);
        setData(res);
      } catch (e) {
        console.error("Failed to load analysis:", e);
      } finally {
        setLoading(false);
      }
    })();
  }, [symbol]);

  if (loading) return <LoadingSkeleton />;
  if (!data) return <Text style={styles.error}>加载失败</Text>;

  const score = data.composite_score ?? 0;
  const scoreColor = score >= 70 ? "#34d399" : score >= 40 ? "#fbbf24" : "#ef4444";

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.back}>← 返回</Text>
        </TouchableOpacity>
      </View>

      {/* Hero score */}
      <View style={styles.hero}>
        <Text style={styles.name}>{data.name}</Text>
        <Text style={styles.symbol}>{data.symbol}</Text>
        <Text style={[styles.heroScore, { color: scoreColor }]}>
          {data.composite_score?.toFixed(1) ?? "--"}
        </Text>
        <Text style={styles.heroLabel}>综合评分</Text>
      </View>

      {/* Score breakdown */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>评分明细</Text>
        <View style={styles.bars}>
          <ScoreBar label="预期收益" value={data.score_breakdown?.predicted_return?.value ?? null} color="#34d399" />
          <ScoreBar label="动量" value={data.score_breakdown?.momentum_score?.value ?? null} color="#60a5fa" />
          <ScoreBar label="质量" value={data.score_breakdown?.quality_score?.value ?? null} color="#fbbf24" />
          <ScoreBar label="情绪" value={data.score_breakdown?.sentiment_score?.value ?? null} color="#c084fc" />
        </View>
      </View>

      {/* Layer scores */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>策略分层</Text>
        <View style={styles.layerGrid}>
          <View style={styles.layerItem}>
            <Text style={styles.layerValue}>{data.layer_scores?.layer1_factor?.toFixed(1) ?? "--"}</Text>
            <Text style={styles.layerLabel}>多因子</Text>
          </View>
          <View style={styles.layerItem}>
            <Text style={styles.layerValue}>{data.layer_scores?.layer2_ml?.toFixed(1) ?? "--"}</Text>
            <Text style={styles.layerLabel}>ML预测</Text>
          </View>
          <View style={styles.layerItem}>
            <Text style={styles.layerValue}>{data.layer_scores?.layer3_event?.toFixed(1) ?? "--"}</Text>
            <Text style={styles.layerLabel}>事件驱动</Text>
          </View>
        </View>
      </View>

      {/* AI Analysis */}
      {data.ai_analysis && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI 深度分析</Text>
          <Text style={styles.aiText}>
            {data.ai_analysis.recommendation ?? "暂无分析"}
          </Text>

          {data.ai_analysis.risk_flags?.length > 0 && (
            <View style={styles.riskFlags}>
              <Text style={styles.riskTitle}>风险提示</Text>
              {data.ai_analysis.risk_flags.map((flag, i) => (
                <Text key={i} style={styles.riskFlag}>• {flag}</Text>
              ))}
            </View>
          )}
        </View>
      )}

      <View style={{ height: 80 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  header: { paddingHorizontal: 20, paddingTop: 60, paddingBottom: 12 },
  back: { fontSize: 16, color: "#34d399" },
  error: { color: "#ef4444", textAlign: "center", marginTop: 100, fontSize: 16 },
  hero: { alignItems: "center", paddingVertical: 24 },
  name: { fontSize: 22, fontWeight: "700", color: "#fff" },
  symbol: { fontSize: 14, color: "#888", marginTop: 4 },
  heroScore: { fontSize: 56, fontWeight: "800", marginTop: 16 },
  heroLabel: { fontSize: 14, color: "#888", marginTop: 4 },
  section: { paddingHorizontal: 20, marginTop: 28 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#fff", marginBottom: 12 },
  bars: { gap: 6 },
  layerGrid: { flexDirection: "row", gap: 12 },
  layerItem: {
    flex: 1,
    backgroundColor: "#111",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
  },
  layerValue: { fontSize: 22, fontWeight: "700", color: "#fff" },
  layerLabel: { fontSize: 12, color: "#888", marginTop: 4 },
  aiText: { fontSize: 14, color: "#ccc", lineHeight: 22 },
  riskFlags: {
    marginTop: 16,
    backgroundColor: "#1a0a0a",
    borderRadius: 12,
    padding: 14,
    borderWidth: 1,
    borderColor: "#3a1a1a",
  },
  riskTitle: { fontSize: 14, fontWeight: "600", color: "#ef4444", marginBottom: 8 },
  riskFlag: { fontSize: 13, color: "#f87171", lineHeight: 22 },
});
