import React, { useState, useEffect, useCallback } from "react";
import {
  View, Text, ScrollView, TouchableOpacity,
  StyleSheet, RefreshControl, Alert,
} from "react-native";
import { useAuth } from "../store/AuthContext";
import { fetchWatchlist, fetchHistory, fetchSystemStatus, logout } from "../services/api";
import type { WatchlistItem, HistoryItem, SystemStatus } from "../types/stock";

export default function ProfileScreen() {
  const { user, signOut } = useAuth();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [w, h, s] = await Promise.all([
        fetchWatchlist(),
        fetchHistory(10),
        fetchSystemStatus(),
      ]);
      setWatchlist(w.items ?? []);
      setHistory(h ?? []);
      setStatus(s);
    } catch (e) {
      console.error("Failed to load profile:", e);
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleLogout = () => {
    Alert.alert("确认退出", "退出后需要重新登录", [
      { text: "取消", style: "cancel" },
      {
        text: "退出",
        style: "destructive",
        onPress: async () => {
          await logout();
          signOut();
        },
      },
    ]);
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); load(); }} tintColor="#34d399" />
      }
    >
      {/* User info */}
      <View style={styles.userCard}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {(user?.nickname ?? user?.phone ?? "?").slice(0, 2)}
          </Text>
        </View>
        <Text style={styles.nickname}>{user?.nickname ?? "用户"}</Text>
        <Text style={styles.phone}>{user?.phone ?? ""}</Text>
      </View>

      {/* System status */}
      {status && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>系统状态</Text>
          <View style={styles.statusGrid}>
            <View style={styles.statusItem}>
              <Text style={styles.statusValue}>{status.stock_count}</Text>
              <Text style={styles.statusLabel}>覆盖股票</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={styles.statusValue}>{status.last_update ?? "--"}</Text>
              <Text style={styles.statusLabel}>最后更新</Text>
            </View>
            <View style={styles.statusItem}>
              <Text style={[styles.statusValue, { color: status.database_ok ? "#34d399" : "#ef4444" }]}>
                {status.database_ok ? "正常" : "异常"}
              </Text>
              <Text style={styles.statusLabel}>数据库</Text>
            </View>
          </View>
        </View>
      )}

      {/* Watchlist */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>我的自选 ({watchlist.length})</Text>
        {watchlist.length === 0 ? (
          <Text style={styles.empty}>暂无自选股票</Text>
        ) : (
          watchlist.slice(0, 5).map((item) => (
            <View key={item.symbol} style={styles.row}>
              <View>
                <Text style={styles.rowName}>{item.name}</Text>
                <Text style={styles.rowSymbol}>{item.symbol}</Text>
              </View>
              <Text style={styles.rowPrice}>
                ¥{item.current_price?.toFixed(2) ?? "--"}
              </Text>
            </View>
          ))
        )}
      </View>

      {/* History */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>推荐历史</Text>
        {history.length === 0 ? (
          <Text style={styles.empty}>暂无历史记录</Text>
        ) : (
          history.slice(0, 5).map((item, i) => (
            <View key={`${item.symbol}-${i}`} style={styles.row}>
              <View>
                <Text style={styles.rowName}>{item.name}</Text>
                <Text style={styles.rowSymbol}>{item.trade_date}</Text>
              </View>
              <Text style={[styles.rowPrice, { color: "#34d399" }]}>
                {item.composite_score?.toFixed(0) ?? "--"}
              </Text>
            </View>
          ))
        )}
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
        <Text style={styles.logoutText}>退出登录</Text>
      </TouchableOpacity>

      <View style={{ height: 120 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  userCard: {
    alignItems: "center",
    paddingTop: 80,
    paddingBottom: 24,
    backgroundColor: "#111",
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: "#34d399",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 12,
  },
  avatarText: { fontSize: 24, fontWeight: "700", color: "#000" },
  nickname: { fontSize: 20, fontWeight: "600", color: "#fff" },
  phone: { fontSize: 14, color: "#888", marginTop: 4 },
  section: { paddingHorizontal: 20, marginTop: 28 },
  sectionTitle: { fontSize: 16, fontWeight: "600", color: "#fff", marginBottom: 12 },
  statusGrid: { flexDirection: "row", gap: 12 },
  statusItem: {
    flex: 1,
    backgroundColor: "#111",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
  },
  statusValue: { fontSize: 16, fontWeight: "700", color: "#fff" },
  statusLabel: { fontSize: 11, color: "#888", marginTop: 4 },
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingVertical: 10,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: "#222",
  },
  rowName: { fontSize: 14, color: "#ccc" },
  rowSymbol: { fontSize: 12, color: "#666", marginTop: 2 },
  rowPrice: { fontSize: 15, fontWeight: "600", color: "#fff" },
  empty: { color: "#666", fontSize: 13, textAlign: "center", paddingVertical: 16 },
  logoutBtn: {
    margin: 20,
    backgroundColor: "#1a1a1a",
    borderRadius: 12,
    padding: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#333",
  },
  logoutText: { color: "#ef4444", fontSize: 15, fontWeight: "500" },
});
