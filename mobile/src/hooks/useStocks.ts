import { useState, useEffect, useCallback } from "react";
import { fetchRecommendations } from "../services/api";
import type { RecommendationsResponse } from "../types/stock";

interface UseStocksResult {
  data: RecommendationsResponse | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  refresh: () => void;
}

export function useStocks(): UseStocksResult {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (isRefresh = false) => {
    try {
      if (isRefresh) setRefreshing(true);
      setError(null);
      const res = await fetchRecommendations();
      setData(res);
    } catch (e: any) {
      setError(e.message ?? "加载失败");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return {
    data,
    loading,
    refreshing,
    error,
    refresh: () => load(true),
  };
}
