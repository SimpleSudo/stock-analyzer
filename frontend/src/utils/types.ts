export interface ChartPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartPointWithIndicators extends ChartPoint {
  // 均线
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
  // KDJ
  kdj_k: number | null;
  kdj_d: number | null;
  kdj_j: number | null;
  // WR
  wr: number | null;
  // OBV
  obv: number | null;
  // ATR
  atr: number | null;
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
  data_source: string;
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

// ── 价格目标 ─────────────────────────────────────────────

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

// ── 行业对比 ─────────────────────────────────────────────

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

// ── 资金流向 ─────────────────────────────────────────────

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

// ── 基本面 ───────────────────────────────────────────────

export interface Fundamental {
  pe: number | null;
  pb: number | null;
  roe: number | null;
  debt_ratio: number | null;
  gross_margin: number | null;
}

// ── 完整响应 ─────────────────────────────────────────────

export interface StockAnalysisResponse {
  symbol: string;
  name?: string;
  data: StockData;
  indicators: Indicators;
  signal: string;
  score: number;
  reasons: string[];
  fundamental?: Fundamental;
  price_targets?: PriceTargets | null;
  industry?: IndustryComparison | null;
  capital_flow?: CapitalFlow | null;
  ai_report?: string | null;
  error?: string;
}

// ── 回测 ─────────────────────────────────────────────────

export interface BacktestTrade {
  date: string;
  action: 'BUY' | 'SELL';
  shares: number;
  price: number;
  cost?: number;
  revenue?: number;
  profit?: number;
}

export interface BacktestPortfolioPoint {
  date: string;
  cash: number;
  shares: number;
  close_price: number;
  portfolio_value: number;
}

export interface BacktestResult {
  symbol: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  final_capital: number;
  total_return: number;
  annualized_return: number;
  max_drawdown: number;
  sharpe_ratio: number;
  win_rate: number;
  total_trades: number;
  trades: BacktestTrade[];
  portfolio_history: BacktestPortfolioPoint[];
  error?: string;
}

// ── 自选股 ───────────────────────────────────────────────

export interface WatchlistItem {
  symbol: string;
  name: string;
  added_at: string;
}

// ── 分析历史 ─────────────────────────────────────────────

export interface HistoryRecord {
  id: number;
  symbol: string;
  name: string;
  signal: string;
  score: number;
  price: number;
  created_at: string;
}

// ── 告警 ─────────────────────────────────────────────────

export interface AlertItem {
  id: string;
  symbol: string;
  target_price: number;
  direction: string;
  note: string | null;
  triggered: number;
  created_at: string;
}

// ── 组合分析 ─────────────────────────────────────────────

export interface PortfolioResult {
  symbols: string[];
  stock_info: Record<string, any>;
  correlation: Record<string, Record<string, number>>;
  individual_stats: Record<string, any>;
  equal_weight_portfolio: {
    annualized_return: number;
    annualized_volatility: number;
    sharpe_ratio: number;
    total_return: number;
  };
  return_curves: any[];
  error?: string;
}
