import { useState, useEffect, useCallback } from "react";
import { fetchStockAnalysis } from "../services/api";
import type { AnalysisDetail } from "../types/stock";

interface UseStockDetailResult {
  data: AnalysisDetail | null;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useStockDetail(symbol: string): UseStockDetailResult {
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!symbol) return;
    try {
      setLoading(true);
      setError(null);
      const res = await fetchStockAnalysis(symbol);
      setData(res);
    } catch (e: any) {
      setError(e.message ?? "加载失败");
    } finally {
      setLoading(false);
    }
  }, [symbol]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, retry: load };
}
