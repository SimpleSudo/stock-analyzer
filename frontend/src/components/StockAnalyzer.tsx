import React, { useState, useEffect } from 'react';
import type { StockAnalysisResponse } from '../utils/types';
import CandlestickChart from './CandlestickChart';
import IndicatorChart from './IndicatorChart';

const StockAnalyzer: React.FC<{
  onAnalyze: (symbol: string) => Promise<void>;
  analysis: StockAnalysisResponse | null;
  loading: boolean;
  error: string | null;
}> = ({ onAnalyze, analysis, loading, error }) => {
  const [symbol, setSymbol] = useState('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [indicatorData, setIndicatorData] = useState<any[]>([]);

  // Fetch chart data when analysis updates
  useEffect(() => {
    if (analysis && analysis.data?.chart) {
      // Transform data for candlestick chart
      const transformedChartData = analysis.data.chart.map((item: any) => ({
        date: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume,
      }));
      setChartData(transformedChartData);
      
      // Transform data for indicator chart - simplified for now
      // In a real app, we would calculate these per data point
      const transformedIndicatorData = analysis.data.chart.map((item: any) => ({
        date: item.date,
        rsi: analysis.indicators?.RSI ?? null,
        macd: analysis.indicators?.MACD ?? null,
        signal: analysis.indicators?.Signal ?? null,
        hist: (analysis.indicators?.MACD ?? 0) - (analysis.indicators?.Signal ?? 0),
        bb_upper: analysis.indicators?.BB_upper ?? null,
        bb_mid: analysis.indicators?.BB_mid ?? null,
        bb_lower: analysis.indicators?.BB_lower ?? null,
      }));
      setIndicatorData(transformedIndicatorData);
    }
  }, [analysis]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (symbol.trim()) {
      await onAnalyze(symbol.trim());
    }
  };

  return (
    <div className="stock-analyzer">
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-group">
          <input
            type="text"
            placeholder="输入股票代码或名称 (如 000001 或 平安银行)"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            disabled={loading}
            className="stock-input"
          />
          <button type="submit" disabled={loading} className="analyze-btn">
            {loading ? '分析中...' : '开始分析'}
          </button>
        </div>
      </form>

      {error && <div className="error-message">{error}</div>}

      {analysis && (
        <div className="analysis-result">
          <div className="result-header">
            <h2>{analysis.symbol} 分析结果</h2>
            <div className="signal-badge">{analysis.signal}</div>
          </div>

          <div className="metrics-grid">
            <div className="metric-card">
              <h3>最新价</h3>
              <p className="price">{analysis.data.latest.price.toFixed(2)}</p>
              <p className="change">
                {analysis.data.latest.change_pct >= 0 ? '+' : ''}
                {analysis.data.latest.change_pct.toFixed(2)}%
              </p>
            </div>

            <div className="metric-card">
              <h3>评分</h3>
              <p className="score">{analysis.score}</p>
              <p className="score-label">(-10 ~ +10)</p>
            </div>

            <div className="metric-card">
              <h3>成交量</h3>
              <p className="volume">{analysis.data.latest.volume.toLocaleString()}</p>
            </div>
          </div>

          <div className="charts-section">
            <CandlestickChart 
              data={chartData}
              ma5={analysis.indicators?.MA5}
              ma10={analysis.indicators?.MA10}
              ma20={analysis.indicators?.MA20}
              ma60={analysis.indicators?.MA60}
            />
            
            <IndicatorChart 
              data={indicatorData}
            />
          </div>

          <div className="reasons-section">
            <h3>分析依据</h3>
            <ul className="reasons-list">
              {analysis.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {!analysis && !loading && !error && (
        <div className="placeholder">
          <p>请输入股票代码或名称开始分析</p>
        </div>
      )}
    </div>
  );
};

export default StockAnalyzer;