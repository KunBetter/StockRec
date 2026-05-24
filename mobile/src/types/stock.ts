// Types migrated from frontend/src/types/stock.ts — shared contract with backend

export interface StockRecommendation {
  symbol: string;
  name: string;
  current_price: number | null;
  price_change_pct: number | null;
  predicted_return: number | null;
  momentum_score: number | null;
  quality_score: number | null;
  sentiment_score: number | null;
  composite_score: number | null;
  rank: number | null;
  risk_level: "low" | "medium" | "high" | null;
  market_cap: number | null;
  holding_period: string | null;
  ai_summary: string | null;
}

export interface RiskSection {
  risk_level: "low" | "medium" | "high";
  label: string;
  description: string;
  stocks: StockRecommendation[];
}

export interface MarketSummary {
  index_name: string;
  index_value: number | null;
  change_pct: number | null;
  market_status: string;
}

export interface RecommendationsResponse {
  date: string;
  generated_at: string | null;
  market_summary: MarketSummary | null;
  sections: RiskSection[];
}

export interface ScoreBreakdown {
  predicted_return?: { value: number; weight: number; contribution: number };
  momentum_score?: { value: number; weight: number; contribution: number };
  quality_score?: { value: number; weight: number; contribution: number };
  sentiment_score?: { value: number; weight: number; contribution: number };
}

export interface AnalysisDetail {
  symbol: string;
  name: string;
  date: string;
  composite_score: number | null;
  score_breakdown: ScoreBreakdown | null;
  layer_scores: {
    layer1_factor: number | null;
    layer2_ml: number | null;
    layer3_event: number | null;
  } | null;
  ai_analysis: {
    recommendation: string | null;
    financial: Record<string, unknown>;
    news: Record<string, unknown>;
    industry: Record<string, unknown>;
    risk_flags: string[];
  } | null;
  key_metrics: Record<string, unknown> | null;
}

// Market types
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

// Profile types
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

export interface SystemStatus {
  last_update: string | null; stock_count: number; watchlist_count: number;
  database_ok: boolean; recent_jobs: JobStatus[];
}

export interface JobStatus {
  job_name: string; status: string; started_at: string | null; duration_ms: number | null;
}

// Auth types
export interface UserInfo {
  user_uuid: string;
  phone: string;
  nickname: string | null;
  avatar_url: string | null;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}
