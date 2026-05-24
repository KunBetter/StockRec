import { useState, useEffect, useCallback } from "react";
import type { RecommendationsResponse } from "../types/stock";
import { fetchRecommendations, type RecParams } from "../services/api";

interface UseStocksResult {
  data: RecommendationsResponse | null;
  loading: boolean;
  error: string | null;
  refetch: (params?: RecParams) => void;
}

export function useStocks(): UseStocksResult {
  const [data, setData] = useState<RecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState<RecParams>({});

  const load = useCallback(async (p?: RecParams) => {
    const merged = p ?? params;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchRecommendations(merged);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    load(params);
  }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const refetch = useCallback((p?: RecParams) => {
    if (p) setParams(p);
    load(p ?? params);
  }, [load, params]);

  return { data, loading, error, refetch };
}
