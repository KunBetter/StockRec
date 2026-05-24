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
