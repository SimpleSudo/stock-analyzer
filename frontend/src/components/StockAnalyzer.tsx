import React, { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import type { StockAnalysisResponse, ChartPointWithIndicators } from '../utils/types';
import StockSearch from './StockSearch';
import AIAssistant from './AIAssistant';
import PDFExportButton from './PDFExportButton';
import PriceTargetCard from './PriceTargetCard';
import IndustryCompareCard from './IndustryCompareCard';
import CapitalFlowChart from './CapitalFlowChart';
import AIReportPanel from './AIReportPanel';
import BacktestPanel from './BacktestPanel';
import WatchlistPanel from './WatchlistPanel';
import HistoryPanel from './HistoryPanel';
import PortfolioPanel from './PortfolioPanel';
import AlertPanel from './AlertPanel';
import { fetchDebate } from '../services/api';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { useWebSocket } from '../hooks/useWebSocket';

const CandlestickChart = lazy(() => import('./CandlestickChart'));
const IndicatorChart = lazy(() => import('./IndicatorChart'));

type Tab = 'analysis' | 'backtest' | 'portfolio' | 'watchlist' | 'history' | 'alerts';

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
  const [activeTab, setActiveTab] = useState<Tab>('analysis');
  const [realtimePrice, setRealtimePrice] = useState<number | null>(null);

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
  ];

  // WebSocket 实时行情
  const wsUrl = analysis?.symbol ? `/ws/realtime/${analysis.symbol}` : null;
  useWebSocket(wsUrl, {
    onMessage: (data) => {
      if (data?.price) setRealtimePrice(data.price);
    },
  });

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
          kdj_k: null, kdj_d: null, kdj_j: null,
          wr: null, obv: null, atr: null,
        })),
      );
    }
    setRealtimePrice(null);
  }, [analysis]);

  // 获取 debate 数据
  useEffect(() => {
    if (analysis?.symbol) {
      const doFetch = async () => {
        setDebateLoading(true);
        try {
          const data = await fetchDebate(analysis.symbol);
          setDebateData(data);
        } catch (err) {
          console.error('获取 debate 数据失败:', err);
        } finally {
          setDebateLoading(false);
        }
      };
      doFetch();
    } else {
      setDebateData(null);
    }
  }, [analysis]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (symbol.trim()) {
        setActiveTab('analysis');
        await onAnalyze(symbol.trim());
      }
    },
    [symbol, onAnalyze],
  );

  const handleSelectStock = useCallback(
    (sym: string) => {
      setSymbol(sym);
      setActiveTab('analysis');
      onAnalyze(sym);
    },
    [onAnalyze],
  );

  // 键盘快捷键
  const shortcuts: { [key: string]: () => void } = {
    'ctrl+k': () => setShowAIAssistant(prev => !prev),
    'ctrl+shift+c': () => setSymbol(''),
    escape: () => { if (showAIAssistant) setShowAIAssistant(false); },
  };
  useKeyboardShortcuts(shortcuts, true);

  const signalClass = analysis?.signal?.includes('买入') ? '买入'
    : analysis?.signal?.includes('卖出') ? '卖出'
    : '观望';

  const displayPrice = realtimePrice ?? analysis?.data?.latest?.price;

  // Tab 配置
  const tabs: { key: Tab; label: string }[] = [
    { key: 'analysis', label: '📊 分析' },
    { key: 'backtest', label: '📈 回测' },
    { key: 'portfolio', label: '🔗 组合' },
    { key: 'watchlist', label: '⭐ 自选' },
    { key: 'history', label: '📜 历史' },
    { key: 'alerts', label: '🔔 告警' },
  ];

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

      {/* Tab 导航 */}
      <div style={{
        display: 'flex', gap: '4px', marginBottom: '16px', borderBottom: '2px solid var(--border-color)',
        paddingBottom: '0', overflowX: 'auto',
      }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '8px 16px', fontSize: '13px', fontWeight: activeTab === tab.key ? 700 : 400,
              border: 'none', borderBottom: activeTab === tab.key ? '2px solid #1a73e8' : '2px solid transparent',
              background: 'transparent', cursor: 'pointer', whiteSpace: 'nowrap',
              color: activeTab === tab.key ? '#1a73e8' : 'var(--text-secondary)',
              marginBottom: '-2px',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* ── 分析 Tab ── */}
      {activeTab === 'analysis' && (
        <>
          {analysis && (
            <div className="analysis-result">
              <div className="result-header">
                <h2>
                  {analysis.name ? `${analysis.name}（${analysis.symbol}）` : analysis.symbol} 分析结果
                </h2>
                <div className={`signal-badge ${signalClass}`}>{analysis.signal}</div>
              </div>

              {analysis.data?.data_source && (
                <p style={{ fontSize: '12px', color: '#999', margin: '4px 0 12px', textAlign: 'right' }}>
                  数据来源：{analysis.data.data_source}（前复权）
                  {realtimePrice && <span style={{ marginLeft: '8px', color: '#1a73e8' }}>🔴 实时</span>}
                </p>
              )}

              <div className="metrics-grid">
                <div className="metric-card">
                  <h3>最新价</h3>
                  <p className="price">{displayPrice?.toFixed(2)}</p>
                  <p className="change" style={{ color: (analysis.data?.latest?.change_pct ?? 0) >= 0 ? '#ef5350' : '#26a69a' }}>
                    {(analysis.data?.latest?.change_pct ?? 0) >= 0 ? '+' : ''}
                    {analysis.data?.latest?.change_pct?.toFixed(2)}%
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
                  <p className="volume">{analysis.data?.latest?.volume?.toLocaleString()}</p>
                </div>
                {analysis.fundamental?.pe != null && (
                  <div className="metric-card">
                    <h3>PE(TTM)</h3>
                    <p className="price" style={{ fontSize: '22px' }}>{analysis.fundamental.pe.toFixed(1)}</p>
                  </div>
                )}
                {analysis.fundamental?.pb != null && (
                  <div className="metric-card">
                    <h3>PB</h3>
                    <p className="price" style={{ fontSize: '22px' }}>{analysis.fundamental.pb.toFixed(2)}</p>
                  </div>
                )}
                {analysis.fundamental?.roe != null && (
                  <div className="metric-card">
                    <h3>ROE</h3>
                    <p className="price" style={{ fontSize: '22px', color: analysis.fundamental.roe > 15 ? '#26a69a' : undefined }}>
                      {analysis.fundamental.roe.toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>

              <div className="charts-section">
                <Suspense fallback={<div style={{ padding: '20px', textAlign: 'center' }}>📊 加载 K 线图...</div>}>
                  <CandlestickChart data={chartData} />
                </Suspense>
                <Suspense fallback={<div style={{ padding: '20px', textAlign: 'center' }}>📈 加载指标图...</div>}>
                  <IndicatorChart data={chartData} />
                </Suspense>
                <PDFExportButton analysis={analysis} />
              </div>

              {analysis.price_targets && (
                <div className="metrics-grid" style={{ marginTop: '16px' }}>
                  <PriceTargetCard priceTargets={analysis.price_targets} />
                </div>
              )}
              {analysis.industry && (
                <div className="metrics-grid" style={{ marginTop: '16px' }}>
                  <IndustryCompareCard industry={analysis.industry} fundamental={analysis.fundamental} />
                </div>
              )}
              {analysis.capital_flow && (
                <div className="metrics-grid" style={{ marginTop: '16px' }}>
                  <CapitalFlowChart capitalFlow={analysis.capital_flow} />
                </div>
              )}
              {analysis.ai_report && (
                <div className="metrics-grid" style={{ marginTop: '16px' }}>
                  <AIReportPanel report={analysis.ai_report} />
                </div>
              )}

              <div className="reasons-section">
                <h3>📋 技术分析依据</h3>
                <ul className="reasons-list">
                  {analysis.reasons.map((reason, index) => (
                    <li key={index}>{reason}</li>
                  ))}
                </ul>
              </div>

              {/* Multi-Agent 辩论区 */}
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
        </>
      )}

      {/* ── 回测 Tab ── */}
      {activeTab === 'backtest' && (
        analysis?.symbol
          ? <BacktestPanel symbol={analysis.symbol} />
          : <div className="placeholder"><p>请先分析一只股票，再进行回测</p></div>
      )}

      {/* ── 组合 Tab ── */}
      {activeTab === 'portfolio' && <PortfolioPanel />}

      {/* ── 自选 Tab ── */}
      {activeTab === 'watchlist' && (
        <WatchlistPanel
          currentSymbol={analysis?.symbol}
          currentName={analysis?.name}
          onSelect={handleSelectStock}
        />
      )}

      {/* ── 历史 Tab ── */}
      {activeTab === 'history' && <HistoryPanel onSelect={handleSelectStock} />}

      {/* ── 告警 Tab ── */}
      {activeTab === 'alerts' && <AlertPanel symbol={analysis?.symbol} />}

      {/* AI 助手 */}
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
