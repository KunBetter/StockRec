import { useState, useCallback } from "react";
import type { AnalysisDetail } from "../types/stock";
import { fetchStockAnalysis } from "../services/api";

interface UseStockDetailResult {
  data: AnalysisDetail | null;
  loading: boolean;
  error: string | null;
  load: (symbol: string) => void;
  close: () => void;
}

export function useStockDetail(): UseStockDetailResult {
  const [data, setData] = useState<AnalysisDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchStockAnalysis(symbol);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "加载详情失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const close = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, load, close };
}
