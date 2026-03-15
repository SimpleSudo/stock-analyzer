import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
});

export const analyzeStock = async (symbol: string) => {
  // Ensure we're only dealing with A-shares (Chinese stocks)
  // Remove any exchange prefixes if present
  const cleanSymbol = symbol.replace(/^(sz|sh)/i, '').replace(/\.[a-z]+$/i, '');
  
  const response = await api.post('/api/analyze', { symbol: cleanSymbol });
  return response.data;
};

export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};
