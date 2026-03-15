import React, { useState } from 'react';
import { StockAnalysisResponse } from '../utils/types';
import { analyzeStock } from '../services/api';

const StockAnalyzer: React.FC<{
  onAnalyze: (symbol: string) => Promise<void>;
  analysis: StockAnalysisResponse | null;
  loading: boolean;
  error: string | null;
}> = ({ onAnalyze, analysis, loading, error }) => {
  const [symbol, setSymbol] = useState('');

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

          <div className="indicators-section">
            <h3>技术指标</h3>
            <div className="indicators-grid">
              <div className="indicator-item">
                <span>MA5:</span> {analysis.indicators.MA5 !== null ? analysis.indicators.MA5.toFixed(2) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>MA10:</span> {analysis.indicators.MA10 !== null ? analysis.indicators.MA10.toFixed(2) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>MA20:</span> {analysis.indicators.MA20 !== null ? analysis.indicators.MA20.toFixed(2) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>MA60:</span> {analysis.indicators.MA60 !== null ? analysis.indicators.MA60.toFixed(2) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>RSI:</span> {analysis.indicators.RSI !== null ? analysis.indicators.RSI.toFixed(2) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>MACD:</span> {analysis.indicators.MACD !== null ? analysis.indicators.MACD.toFixed(4) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>布林上轨:</span> {analysis.indicators.BB_upper !== null ? analysis.indicators.BB_upper.toFixed(2) : 'N/A'}
              </div>
              <div className="indicator-item">
                <span>布林下轨:</span> {analysis.indicators.BB_lower !== null ? analysis.indicators.BB_lower.toFixed(2) : 'N/A'}
              </div>
            </div>
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
