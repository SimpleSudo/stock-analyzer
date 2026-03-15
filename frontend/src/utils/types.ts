export interface StockData {
  latest: {
    price: number;
    change: number;
    change_pct: number;
    volume: number;
    amount: number;
  };
  chart: Array<{
    date: string;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

export interface Indicators {
  MA5: number | null;
  MA10: number | null;
  MA20: number | null;
  MA60: number | null;
  RSI: number | null;
  MACD: number | null;
  Signal: number | null;
  BB_upper: number | null;
  BB_mid: number | null;
  BB_lower: number | null;
}

export interface StockAnalysisResponse {
  symbol: string;
  data: StockData;
  indicators: Indicators;
  signal: string;
  score: number;
  reasons: string[];
  error?: string;
}
