import React, { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import type { StockAnalysisResponse, ChartPointWithIndicators } from '../utils/types';
import StockSearch from './StockSearch';
import AIAssistant from './AIAssistant';
import PDFExportButton from './PDFExportButton';
import PriceTargetCard from './PriceTargetCard';
import IndustryCompareCard from './IndustryCompareCard';
import CapitalFlowChart from './CapitalFlowChart';
import AIReportPanel from './AIReportPanel';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';

const CandlestickChart = lazy(() => import('./CandlestickChart'));
const IndicatorChart = lazy(() => import('./IndicatorChart'));

const StockAnalyzer: React.FC<{
  onAnalyze: (symbol: string) => Promise<void>;
  analysis: StockAnalysisResponse | null;
  loading: boolean;
  error: string | null;
}> = ({ onAnalyze, analysis, loading, error }) => {
  const [symbol, setSymbol] = useState('');
  const [chartData, setChartData] = useState<ChartPointWithIndicators[]>([]);
  const [showAIAssistant, setShowAIAssistant] = useState(false);
  const [debateData, setDebateData] = useState<any>(null);
  const [debateLoading, setDebateLoading] = useState(false);

  // A 股热门股票列表
  const popularStocks = [
    { symbol: '000001', name: '平安银行' },
    { symbol: '000002', name: '万科A' },
    { symbol: '000651', name: '格力电器' },
    { symbol: '000858', name: '五粮液' },
    { symbol: '002415', name: '海康威视' },
    { symbol: '300059', name: '东方财富' },
    { symbol: '600000', name: '浦发银行' },
    { symbol: '600036', name: '招商银行' },
    { symbol: '600519', name: '贵州茅台' },
    { symbol: '600887', name: '伊利股份' },
    { symbol: '601318', name: '中国平安' },
    { symbol: '601398', name: '工商银行' },
    { symbol: '601857', name: '中国石油' },
    { symbol: '601988', name: '中国银行' },
  ];

  // 当 analysis 更新时，使用 chart_with_indicators（含历史指标序列）
  useEffect(() => {
    if (analysis?.data?.chart_with_indicators) {
      setChartData(analysis.data.chart_with_indicators);
    } else if (analysis?.data?.chart) {
      setChartData(
        analysis.data.chart.map(item => ({
          ...item,
          ma5: null, ma10: null, ma20: null, ma60: null,
          rsi: null, macd: null, signal: null, hist: null,
          bb_upper: null, bb_mid: null, bb_lower: null,
        })),
      );
    }
  }, [analysis]);

  // 获取 debate（多 Agent 辩论）数据
  useEffect(() => {
    if (analysis?.symbol) {
      const fetchDebate = async () => {
        setDebateLoading(true);
        try {
          const response = await fetch('/api/analyze/debate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: analysis.symbol }),
          });
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          const data = await response.json();
          setDebateData(data);
        } catch (err) {
          console.error('获取 debate 数据失败:', err);
        } finally {
          setDebateLoading(false);
        }
      };
      fetchDebate();
    } else {
      setDebateData(null);
    }
  }, [analysis]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (symbol.trim()) {
        await onAnalyze(symbol.trim());
      }
    },
    [symbol, onAnalyze],
  );

  // 键盘快捷键
  const shortcuts: { [key: string]: () => void } = {
    'ctrl+k': () => setShowAIAssistant(prev => !prev),
    'ctrl+p': () => {
      if (analysis) {
        const btn = document.querySelector<HTMLElement>('.pdf-export-btn');
        btn?.click();
      }
    },
    'ctrl+shift+c': () => setSymbol(''),
    escape: () => {
      if (showAIAssistant) setShowAIAssistant(false);
    },
  };
  useKeyboardShortcuts(shortcuts, true);

  // 信号徽章颜色
  const signalClass = analysis?.signal?.includes('买入') ? '买入'
    : analysis?.signal?.includes('卖出') ? '卖出'
    : '观望';

  return (
    <div className="stock-analyzer">
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-group">
          <StockSearch
            value={symbol}
            onChange={setSymbol}
            onSelect={setSymbol}
            popularStocks={popularStocks}
          />
          <button type="submit" disabled={loading || !symbol.trim()} className="analyze-btn">
            {loading ? '分析中...' : '开始分析'}
          </button>
        </div>
      </form>

      {error && <div className="error-message">⚠️ {error}</div>}

      {analysis && (
        <div className="analysis-result">
          <div className="result-header">
            <h2>
              {analysis.name ? `${analysis.name}（${analysis.symbol}）` : analysis.symbol} 分析结果
            </h2>
            <div className={`signal-badge ${signalClass}`}>{analysis.signal}</div>
          </div>

          {/* 数据来源标注 */}
          {analysis.data?.data_source && (
            <p style={{ fontSize: '12px', color: '#999', margin: '4px 0 12px', textAlign: 'right' }}>
              数据来源：{analysis.data.data_source}（前复权）
            </p>
          )}

          <div className="metrics-grid">
            <div className="metric-card">
              <h3>最新价</h3>
              <p className="price">{analysis.data.latest.price.toFixed(2)}</p>
              <p className="change" style={{ color: analysis.data.latest.change_pct >= 0 ? '#ef5350' : '#26a69a' }}>
                {analysis.data.latest.change_pct >= 0 ? '+' : ''}
                {analysis.data.latest.change_pct.toFixed(2)}%
              </p>
            </div>

            <div className="metric-card">
              <h3>技术评分</h3>
              <p className="score" style={{ color: analysis.score > 0 ? '#ef5350' : analysis.score < 0 ? '#26a69a' : '#999' }}>
                {analysis.score > 0 ? `+${analysis.score}` : analysis.score}
              </p>
              <p className="score-label">技术信号</p>
            </div>

            <div className="metric-card">
              <h3>成交量</h3>
              <p className="volume">{analysis.data.latest.volume.toLocaleString()}</p>
            </div>

            {/* 基本面快速概览 */}
            {analysis.fundamental && (
              <>
                {analysis.fundamental.pe != null && (
                  <div className="metric-card">
                    <h3>PE(TTM)</h3>
                    <p className="price" style={{ fontSize: '22px' }}>{analysis.fundamental.pe.toFixed(1)}</p>
                  </div>
                )}
                {analysis.fundamental.pb != null && (
                  <div className="metric-card">
                    <h3>PB</h3>
                    <p className="price" style={{ fontSize: '22px' }}>{analysis.fundamental.pb.toFixed(2)}</p>
                  </div>
                )}
                {analysis.fundamental.roe != null && (
                  <div className="metric-card">
                    <h3>ROE</h3>
                    <p className="price" style={{ fontSize: '22px', color: analysis.fundamental.roe > 15 ? '#26a69a' : undefined }}>
                      {analysis.fundamental.roe.toFixed(1)}%
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* ── K线图 + 技术指标图 ── */}
          <div className="charts-section">
            <Suspense fallback={<div style={{ padding: '20px', textAlign: 'center' }}>📊 加载 K 线图...</div>}>
              <CandlestickChart data={chartData} />
            </Suspense>

            <Suspense fallback={<div style={{ padding: '20px', textAlign: 'center' }}>📈 加载指标图...</div>}>
              <IndicatorChart data={chartData} />
            </Suspense>

            <PDFExportButton analysis={analysis} />
          </div>

          {/* ── 价格目标 ── */}
          {analysis.price_targets && (
            <div className="metrics-grid" style={{ marginTop: '16px' }}>
              <PriceTargetCard priceTargets={analysis.price_targets} />
            </div>
          )}

          {/* ── 行业对比 ── */}
          {analysis.industry && (
            <div className="metrics-grid" style={{ marginTop: '16px' }}>
              <IndustryCompareCard industry={analysis.industry} fundamental={analysis.fundamental} />
            </div>
          )}

          {/* ── 资金流向 ── */}
          {analysis.capital_flow && (
            <div className="metrics-grid" style={{ marginTop: '16px' }}>
              <CapitalFlowChart capitalFlow={analysis.capital_flow} />
            </div>
          )}

          {/* ── AI 分析报告 ── */}
          {analysis.ai_report && (
            <div className="metrics-grid" style={{ marginTop: '16px' }}>
              <AIReportPanel report={analysis.ai_report} />
            </div>
          )}

          {/* ── 技术分析依据 ── */}
          <div className="reasons-section">
            <h3>📋 技术分析依据</h3>
            <ul className="reasons-list">
              {analysis.reasons.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>

          {/* ── Multi-Agent 辩论区 ── */}
          {debateData?.agent_outputs && (
            <div className="debate-section">
              <h3>🤖 智能体辩论过程</h3>
              {debateLoading && <p style={{ color: '#999' }}>加载中...</p>}
              <div className="debate-grid">
                {Object.entries(debateData.agent_outputs).map(([agentName, agentOutput]: [string, any]) => (
                  <div key={agentName} className="debate-card">
                    <h4>{agentName} Agent</h4>
                    <p>
                      <strong>信号：</strong>
                      <span style={{ color: agentOutput.signal?.includes('买入') ? '#ef5350' : agentOutput.signal?.includes('卖出') ? '#26a69a' : '#999' }}>
                        {agentOutput.signal}
                      </span>
                    </p>
                    <p><strong>评分：</strong>{agentOutput.score}</p>
                    {agentOutput.indicators && Object.keys(agentOutput.indicators).length > 0 && (
                      <p>
                        <strong>关键指标：</strong>
                        {Object.entries(agentOutput.indicators).map(([k, v]: [string, any]) => (
                          <span key={k} className="indicator-item">{k}: {v}</span>
                        ))}
                      </p>
                    )}
                    <details>
                      <summary style={{ cursor: 'pointer', color: '#666' }}>查看分析理由</summary>
                      <ul>
                        {agentOutput.reasons?.map((r: string, i: number) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </details>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!analysis && !loading && !error && (
        <div className="placeholder">
          <p>🔍 请输入股票代码或名称开始分析</p>
          <p style={{ fontSize: '12px', color: '#999' }}>支持代码搜索（如 000001）或名称搜索（如 平安银行）</p>
        </div>
      )}

      {(analysis || loading) && (
        <AIAssistant
          analysis={analysis}
          show={showAIAssistant}
          onClose={() => setShowAIAssistant(false)}
        />
      )}

      {!loading && analysis && (
        <button
          className="ai-toggle-btn"
          onClick={() => setShowAIAssistant(prev => !prev)}
          title="快捷键：Ctrl+K"
        >
          {showAIAssistant ? '关闭 AI 助手' : '🤖 AI 分析助手'}
        </button>
      )}
    </div>
  );
};

export default StockAnalyzer;
