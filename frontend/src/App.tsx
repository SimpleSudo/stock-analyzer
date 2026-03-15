import React from 'react';
import { analyzeStock } from './services/api';
import type { StockAnalysisResponse } from './utils/types';
import StockAnalyzer from './components/StockAnalyzer';
import './App.css';

function App() {
  const [analysis, setAnalysis] = React.useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleAnalyze = async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeStock(symbol);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>📈 A股智能分析系统</h1>
        <p>输入股票代码或名称，获取多维度AI分析与买入建议</p>
      </header>
      <main>
        <StockAnalyzer 
          onAnalyze={handleAnalyze} 
          analysis={analysis} 
          loading={loading} 
          error={error} 
        />
      </main>
    </div>
  );
}

export default App;