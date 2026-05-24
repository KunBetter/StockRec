import type { RecommendationsResponse, AnalysisDetail } from "../types/stock";

const BASE = "/api/v1";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined) url.searchParams.set(k, v);
    });
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// Recommendations
export interface RecParams {
  date?: string;
  price_min?: number;
  price_max?: number;
  limit?: number;
}
export function fetchRecommendations(params?: RecParams): Promise<RecommendationsResponse> {
  const q: Record<string, string> = {};
  if (params?.date) q.target_date = params.date;
  if (params?.price_min !== undefined && params.price_min !== null) q.price_min = String(params.price_min);
  if (params?.price_max !== undefined && params.price_max !== null) q.price_max = String(params.price_max);
  if (params?.limit) q.limit = String(params.limit);
  return get<RecommendationsResponse>("/recommendations", q);
}

// Analysis
export function fetchStockAnalysis(symbol: string, date?: string): Promise<AnalysisDetail> {
  return get<AnalysisDetail>(`/analysis/${symbol}`, date ? { target_date: date } : {});
}

// Health
export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE}/health`);
    const data = await res.json();
    return data.status === "ok";
  } catch {
    return false;
  }
}

// Market
export function fetchMarketOverview(): Promise<MarketOverviewResponse> {
  return get<MarketOverviewResponse>("/market/overview");
}

export interface MarketOverviewResponse {
  date: string;
  indices: IndexItem[];
  breadth: MarketBreadth;
  sectors: SectorItem[];
  top_gainers: MoverItem[];
  top_losers: MoverItem[];
}

export interface IndexItem {
  name: string; code: string; value: number; change_pct: number; change_amount: number;
}
export interface MarketBreadth {
  up: number; down: number; flat: number; up_pct: number; down_pct: number;
  volume_billion: number; limit_up: number; limit_down: number;
}
export interface SectorItem {
  name: string; change_pct: number; leader: string; leader_change: number;
}
export interface MoverItem {
  symbol: string; name: string; change_pct: number;
}

// Profile
export interface WatchlistItem {
  symbol: string; name: string; industry: string | null; market_cap: number | null;
  current_price: number | null; price_change_pct: number | null;
  composite_score: number | null; risk_level: string | null;
}
export interface WatchlistResponse { count: number; items: WatchlistItem[]; }

export interface HistoryItem {
  symbol: string; name: string; trade_date: string | null;
  composite_score: number | null; predicted_return: number | null;
  risk_level: string | null; rank: number | null; ai_summary: string | null;
}
export interface HistoryResponse extends Array<HistoryItem> {}

export interface SystemStatus {
  last_update: string | null; stock_count: number; watchlist_count: number;
  database_ok: boolean; recent_jobs: { job_name: string; status: string; started_at: string | null; duration_ms: number | null }[];
}

export function fetchWatchlist(): Promise<WatchlistResponse> {
  return get<WatchlistResponse>("/profile/watchlist");
}
export function addToWatchlist(symbol: string): Promise<{ success: boolean; symbol: string }> {
  return post(`/profile/watchlist/${symbol}`);
}
export function removeFromWatchlist(symbol: string): Promise<{ success: boolean; symbol: string }> {
  return del(`/profile/watchlist/${symbol}`);
}
export function fetchRecommendationHistory(limit?: number): Promise<HistoryItem[]> {
  return get<HistoryItem[]>(`/profile/history?limit=${limit || 30}`);
}
export function fetchSystemStatus(): Promise<SystemStatus> {
  return get<SystemStatus>("/profile/status");
}
