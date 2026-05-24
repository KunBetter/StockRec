import { MMKV } from "react-native-mmkv";
import config from "./config";

const BASE = config.apiBaseUrl;
const storage = new MMKV({ id: "stockrec-auth" });

// Token management
export function getAccessToken(): string | null {
  return storage.getString("access_token") ?? null;
}

export function getRefreshToken(): string | null {
  return storage.getString("refresh_token") ?? null;
}

export function saveTokens(access: string, refresh: string): void {
  storage.set("access_token", access);
  storage.set("refresh_token", refresh);
}

export function clearTokens(): void {
  storage.delete("access_token");
  storage.delete("refresh_token");
}

// HTTP client
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      headers["Authorization"] = `Bearer ${getAccessToken()}`;
      const retry = await fetch(`${BASE}${path}`, { ...options, headers });
      if (!retry.ok) throw new Error(`API error: ${retry.status}`);
      return retry.json();
    }
    clearTokens();
    throw new Error("Unauthorized");
  }

  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

async function tryRefreshToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

// Auth
import type { LoginResponse, TokenResponse } from "../types/stock";

export async function login(phone: string, code: string): Promise<LoginResponse> {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, code }),
  });
  if (!res.ok) throw new Error("Login failed");
  const data: LoginResponse = await res.json();
  saveTokens(data.access_token, data.refresh_token);
  return data;
}

export async function logout(): Promise<void> {
  try {
    await request("/auth/logout", { method: "POST" });
  } finally {
    clearTokens();
  }
}

// Recommendations
import type { RecommendationsResponse, AnalysisDetail, RecParams } from "../types/stock";

export function fetchRecommendations(params?: RecParams): Promise<RecommendationsResponse> {
  const q = new URLSearchParams();
  if (params?.date) q.set("target_date", params.date);
  if (params?.price_min !== undefined) q.set("price_min", String(params.price_min));
  if (params?.price_max !== undefined) q.set("price_max", String(params.price_max));
  if (params?.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  return request(`/recommendations${qs ? `?${qs}` : ""}`);
}

export function fetchStockAnalysis(symbol: string, date?: string): Promise<AnalysisDetail> {
  const qs = date ? `?target_date=${date}` : "";
  return request(`/analysis/${symbol}${qs}`);
}

// Market
export function fetchMarketOverview(): Promise<MarketOverviewResponse> {
  return request("/market/overview");
}

// Profile
export function fetchWatchlist(): Promise<WatchlistResponse> {
  return request("/profile/watchlist");
}

export function addToWatchlist(symbol: string): Promise<{ success: boolean }> {
  return request(`/profile/watchlist/${symbol}`, { method: "POST" });
}

export function removeFromWatchlist(symbol: string): Promise<{ success: boolean }> {
  return request(`/profile/watchlist/${symbol}`, { method: "DELETE" });
}

export function fetchHistory(limit = 30): Promise<HistoryItem[]> {
  return request(`/profile/history?limit=${limit}`);
}

export function fetchSystemStatus(): Promise<SystemStatus> {
  return request("/profile/status");
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
