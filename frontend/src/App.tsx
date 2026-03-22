import React, { lazy, Suspense } from 'react';
import { analyzeStock } from './services/api';
import type { StockAnalysisResponse } from './utils/types';
import { useTheme } from './hooks/useTheme';
import './App.css';

const StockAnalyzer = lazy(() => import('./components/StockAnalyzer'));

function App() {
  const [analysis, setAnalysis] = React.useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const { theme, toggleTheme } = useTheme();

  const handleAnalyze = async (symbol: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeStock(symbol);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '分析失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App" data-theme={theme}>
      <header className="App-header">
        <div className="header-content">
          <div>
            <h1>📈 A股智能分析系统</h1>
            <p>输入股票代码或名称，获取多维度 AI 分析与操作建议</p>
          </div>
          <button
            onClick={toggleTheme}
            className="theme-toggle"
            title={`切换到${theme === 'light' ? '深色' : '浅色'}模式`}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>
      <main>
        <Suspense fallback={<div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>加载中...</div>}>
          <StockAnalyzer
            onAnalyze={handleAnalyze}
            analysis={analysis}
            loading={loading}
            error={error}
          />
        </Suspense>
      </main>
    </div>
  );
}

export default App;
