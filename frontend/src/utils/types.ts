export interface ChartPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartPointWithIndicators extends ChartPoint {
  // 均线（每个历史数据点都有值）
  ma5: number | null;
  ma10: number | null;
  ma20: number | null;
  ma60: number | null;
  // RSI
  rsi: number | null;
  // MACD
  macd: number | null;
  signal: number | null;
  hist: number | null;
  // 布林带
  bb_upper: number | null;
  bb_mid: number | null;
  bb_lower: number | null;
}

export interface StockData {
  latest: {
    price: number;
    change: number;
    change_pct: number;
    volume: number;
    amount: number;
  };
  chart: ChartPoint[];
  chart_with_indicators: ChartPointWithIndicators[];
  data_source: string;  // "AKShare" | "Tushare"
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

// ── 价格目标 ─────────────────────────────────────────────────────────────────

export interface PriceTimeframe {
  buy_zone: [number, number];
  stop_loss: number;
  targets: [number, number, number];
  risk_reward: number;
  potential_pct: number;
  horizon: string;
  basis: string;
}

export interface PriceTargets {
  current_price: number;
  short_term: PriceTimeframe;
  medium_term: PriceTimeframe;
  long_term: PriceTimeframe;
}

// ── 行业对比 ─────────────────────────────────────────────────────────────────

export interface IndustryComparison {
  industry_name: string;
  peer_count: number;
  stock_pe: number | null;
  industry_median_pe: number | null;
  pe_percentile: number | null;
  stock_pb: number | null;
  industry_median_pb: number | null;
  pb_percentile: number | null;
  stock_roe: number | null;
  industry_median_roe: number | null;
  valuation_verdict: string;
}

// ── 资金流向 ─────────────────────────────────────────────────────────────────

export interface CapitalFlowPoint {
  date: string;
  close: number | null;
  change_pct: number | null;
  main_net: number;
  retail_net: number;
}

export interface CapitalFlow {
  today_main_net: number;
  five_day_main_net: number;
  ten_day_main_net: number;
  today_retail_net: number;
  main_trend: string;
  retail_vs_main: string;
  history: CapitalFlowPoint[];
}

// ── 基本面 ───────────────────────────────────────────────────────────────────

export interface Fundamental {
  pe: number | null;
  pb: number | null;
  roe: number | null;
  debt_ratio: number | null;
  gross_margin: number | null;
}

// ── 完整响应 ─────────────────────────────────────────────────────────────────

export interface StockAnalysisResponse {
  symbol: string;
  name?: string;
  data: StockData;
  indicators: Indicators;
  signal: string;
  score: number;
  reasons: string[];
  // 新增多维度分析字段（可能为 null，表示获取失败或未配置）
  fundamental?: Fundamental;
  price_targets?: PriceTargets | null;
  industry?: IndustryComparison | null;
  capital_flow?: CapitalFlow | null;
  ai_report?: string | null;
  error?: string;
}
