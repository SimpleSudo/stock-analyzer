import axios from 'axios';
import type {
  BacktestResult,
  WatchlistItem,
  HistoryRecord,
  AlertItem,
  PortfolioResult,
} from '../utils/types';

const api = axios.create({ baseURL: '' });

// ── 清理股票代码 ────────────────────────────────────────
const cleanCode = (symbol: string) =>
  symbol.replace(/^(sz|sh)/i, '').replace(/\.[a-zA-Z]+$/, '').trim();

// ── 核心分析 ────────────────────────────────────────────
export const analyzeStock = async (symbol: string) => {
  const response = await api.post('/api/analyze', { symbol: cleanCode(symbol) });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

// ── 多 Agent 辩论 ───────────────────────────────────────
export const fetchDebate = async (symbol: string) => {
  const response = await api.post('/api/analyze/debate', { symbol: cleanCode(symbol) });
  return response.data;
};

// ── 回测 ────────────────────────────────────────────────
export const runBacktest = async (
  symbol: string,
  startDate?: string,
  endDate?: string,
  initialCapital?: number,
): Promise<BacktestResult> => {
  const response = await api.post('/api/backtest/run', {
    symbol: cleanCode(symbol),
    start_date: startDate,
    end_date: endDate,
    initial_capital: initialCapital ?? 100000,
  });
  return response.data;
};

// ── 自选股 ──────────────────────────────────────────────
export const getWatchlist = async (): Promise<WatchlistItem[]> => {
  const response = await api.get('/api/v1/watchlist');
  return response.data.watchlist;
};

export const addToWatchlist = async (symbol: string, name?: string) => {
  const response = await api.post('/api/v1/watchlist', { symbol: cleanCode(symbol), name });
  return response.data;
};

export const removeFromWatchlist = async (symbol: string) => {
  const response = await api.delete(`/api/v1/watchlist/${cleanCode(symbol)}`);
  return response.data;
};

// ── 分析历史 ────────────────────────────────────────────
export const getHistory = async (symbol?: string, limit = 50): Promise<HistoryRecord[]> => {
  const params: any = { limit };
  if (symbol) params.symbol = cleanCode(symbol);
  const response = await api.get('/api/v1/history', { params });
  return response.data.records;
};

// ── AI 对话 ─────────────────────────────────────────────
export const aiChat = async (question: string, symbol?: string, context?: any) => {
  const response = await api.post('/api/v1/ai/chat', {
    question,
    symbol: symbol ? cleanCode(symbol) : undefined,
    context,
  });
  return response.data.reply;
};

// ── 组合分析 ─────────────────────────────────────────────
export const analyzePortfolio = async (symbols: string[]): Promise<PortfolioResult> => {
  const response = await api.post('/api/v1/analyze/portfolio', {
    symbols: symbols.map(cleanCode),
  });
  return response.data;
};

// ── 告警 ─────────────────────────────────────────────────
export const getAlerts = async (symbol?: string): Promise<AlertItem[]> => {
  const params = symbol ? { symbol: cleanCode(symbol) } : {};
  const response = await api.get('/api/v1/alerts', { params });
  return response.data.alerts;
};

export const createAlert = async (symbol: string, targetPrice: number, direction = 'above', note?: string) => {
  const response = await api.post('/api/v1/alerts', {
    symbol: cleanCode(symbol),
    target_price: targetPrice,
    direction,
    note,
  });
  return response.data;
};

export const deleteAlert = async (alertId: string) => {
  const response = await api.delete(`/api/v1/alerts/${alertId}`);
  return response.data;
};

// ── 搜索 ─────────────────────────────────────────────────
export const searchStocks = async (q: string) => {
  const response = await api.get('/api/search', { params: { q } });
  return response.data.results;
};
