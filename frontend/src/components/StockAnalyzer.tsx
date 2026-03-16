import React, { useState, useEffect, useCallback } from 'react';
import type { StockAnalysisResponse } from '../utils/types';
import CandlestickChart from './CandlestickChart';
import IndicatorChart from './IndicatorChart';
import StockSearch from './StockSearch';
import AIAssistant from './AIAssistant';
import PDFExportButton from './PDFExportButton';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

// TODO: Consider adding lazy loading for heavy components to improve initial load time

const StockAnalyzer: React.FC<{
  onAnalyze: (symbol: string) => Promise<void>;
  analysis: StockAnalysisResponse | null;
  loading: boolean;
  error: string | null;
}> = ({ onAnalyze, analysis, loading, error }) => {
  const [symbol, setSymbol] = useState('');
  const [chartData, setChartData] = useState<any[]>([]);
  const [indicatorData, setIndicatorData] = useState<any[]>([]);
  const [showAIAssistant, setShowAIAssistant] = useState(false);

  // A-share popular stocks for search dropdown
  const popularStocks = [
    { symbol: '000001', name: '平安银行' },
    { symbol: '000002', name: '万科A' },
    { symbol: '000858', name: '五粮液' },
    { symbol: '600000', name: '浦发银行' },
    { symbol: '600036', name: '招商银行' },
    { symbol: '600519', name: '贵州茅台' },
    { symbol: '600887', name: '伊利股份' },
    { symbol: '601318', name: '中国平安' },
    { symbol: '601398', name: '工商银行' },
    { symbol: '601857', name: '中国石油' },
    { symbol: '601988', name: '中国银行' },
    { symbol: '000651', name: '格力电器' },
    { symbol: '000858', name: '五粮液' },
    { symbol: '002415', name: '海康威视' },
    { symbol: '300059', name: '东方财富' },
  ];

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

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (symbol.trim()) {
      await onAnalyze(symbol.trim());
    }
  }, [symbol, onAnalyze]);

  // Keyboard shortcuts configuration
  const shortcuts: { [key: string]: () => void } = {
    'enter': () => {
      // Trigger form submit when Enter is pressed in search
      // This is handled naturally by the form
    },
    'ctrl+l': () => {
      // Focus on search input - we can't directly focus without ref, but we can select all text if input exists
      // For simplicity, we'll just note the intent; actual focus would require a ref
      console.log('Focus search shortcut triggered (would focus input if ref available)');
    },
    'ctrl+k': () => {
      // Toggle AI assistant
      setShowAIAssistant(!showAIAssistant);
    },
    'ctrl+p': () => {
      // Export PDF if analysis exists
      if (analysis) {
        // Find and click the PDF export button
        const pdfButton = document.querySelector('.pdf-export-btn');
        if (pdfButton) {
          (pdfButton as HTMLElement).click();
        }
      }
    },
    'ctrl+shift+c': () => {
      // Clear search
      setSymbol('');
      // Note: focusing would require ref, omitted for simplicity
    },
    'escape': () => {
      // Close AI assistant if open
      if (showAIAssistant) {
        setShowAIAssistant(false);
      }
    }
  };

  useKeyboardShortcuts(shortcuts, true);

  return (
    <div className="stock-analyzer">
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-group">
          <StockSearch
            onSelect={setSymbol}
            popularStocks={popularStocks}
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
            
            {analysis && (
              <PDFExportButton 
                analysis={analysis}
              />
            )}
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

      {(analysis || loading) && (
        <AIAssistant
          analysis={analysis}
          show={showAIAssistant}
          onClose={() => setShowAIAssistant(false)}
        />
      )}

      {/* AI Assistant toggle button */}
      {!loading && analysis && (
        <button 
          className="ai-toggle-btn"
          onClick={() => setShowAIAssistant(!showAIAssistant)}
        >
          {showAIAssistant ? '关闭AI助手' : 'AI分析助手'}
        </button>
      )}
    </div>
  );
};

export default StockAnalyzer;