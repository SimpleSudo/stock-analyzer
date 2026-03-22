import axios from 'axios';

// 不设置 baseURL，直接使用相对路径，避免双重 /api 前缀问题
// vite.config.ts 已配置将 /api 代理到 http://localhost:8000
const api = axios.create({
  baseURL: '',
});

export const analyzeStock = async (symbol: string) => {
  // 清理股票代码：去除交易所前缀（如 sz/sh）和后缀（如 .SZ/.SH）
  const cleanSymbol = symbol.replace(/^(sz|sh)/i, '').replace(/\.[a-zA-Z]+$/, '').trim();
  const response = await api.post('/api/analyze', { symbol: cleanSymbol });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

export const runBacktest = async (
  symbol: string,
  startDate?: string,
  endDate?: string,
  initialCapital?: number,
) => {
  const cleanSymbol = symbol.replace(/^(sz|sh)/i, '').replace(/\.[a-zA-Z]+$/, '').trim();
  const response = await api.post('/api/backtest/run', {
    symbol: cleanSymbol,
    start_date: startDate,
    end_date: endDate,
    initial_capital: initialCapital ?? 100000,
  });
  return response.data;
};
