import type { RecommendationsResponse, AnalysisDetail, BriefingResponse, CompareRequest, CompareResponse, ChatRequest, DataFreshness, MarketOverviewResponse, IndexItem, MarketBreadth, SectorItem, MoverItem, WatchlistItem, WatchlistResponse, HistoryItem, SystemStatus } from "../types/stock";

const BASE = "/api/v1";

async function get<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) Object.entries(params).forEach(([k, v]) => { if (v !== undefined) url.searchParams.set(k, v); });
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export interface RecParams { date?: string; price_min?: number; price_max?: number; limit?: number; sort_by?: string; sort_order?: string; industry?: string; pe_min?: number; pe_max?: number; dividend_min?: number; risk_level?: string; }

export function fetchRecommendations(params?: RecParams): Promise<RecommendationsResponse> {
  const q: Record<string, string> = {};
  if (params) Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null) q[k] = String(v); });
  return get<RecommendationsResponse>("/recommendations", q);
}

export function fetchBriefing(): Promise<BriefingResponse> {
  return get<BriefingResponse>("/recommendations/briefing");
}

export function fetchStockAnalysis(symbol: string, date?: string): Promise<AnalysisDetail> {
  return get<AnalysisDetail>(`/analysis/${symbol}`, date ? { target_date: date } : {});
}

export function fetchPeers(symbol: string): Promise<{ symbol: string; peers: import("../types/stock").PeerStock[] }> {
  return get(`/recommendations/${symbol}/peers`);
}

export function fetchCompare(symbols: string[]): Promise<CompareResponse> {
  return post<CompareResponse>("/stocks/compare", { symbols } as CompareRequest);
}

export function checkHealth(): Promise<boolean> {
  return get<{ status: string }>("/health").then(d => d.status === "ok").catch(() => false);
}

export function fetchMarketOverview(): Promise<MarketOverviewResponse> {
  return get<MarketOverviewResponse>("/market/overview");
}

export function fetchWatchlist(): Promise<WatchlistResponse> { return get<WatchlistResponse>("/profile/watchlist"); }
export function addToWatchlist(symbol: string): Promise<{ success: boolean; symbol: string }> { return post(`/profile/watchlist/${symbol}`); }
export function removeFromWatchlist(symbol: string): Promise<{ success: boolean; symbol: string }> { return del(`/profile/watchlist/${symbol}`); }
export function fetchRecommendationHistory(limit?: number): Promise<HistoryItem[]> { return get<HistoryItem[]>(`/profile/history?limit=${limit || 30}`); }
export function fetchSystemStatus(): Promise<SystemStatus> { return get<SystemStatus>("/profile/status"); }
export function fetchDataFreshness(): Promise<DataFreshness> { return get<DataFreshness>("/data/freshness"); }
