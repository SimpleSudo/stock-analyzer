import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
  ReferenceLine,
} from 'recharts';
import { runBacktest } from '../services/api';
import type { BacktestResult } from '../utils/types';

interface Props {
  symbol: string;
}

const BacktestPanel: React.FC<Props> = ({ symbol }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [capital, setCapital] = useState('100000');
  const [result, setResult] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBacktest(
        symbol,
        startDate || undefined,
        endDate || undefined,
        Number(capital) || 100000,
      );
      if (res.error) {
        setError(res.error);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '回测失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="backtest-panel">
      <h3>📊 策略回测</h3>

      <div className="backtest-inputs" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <input
          type="date"
          value={startDate}
          onChange={e => setStartDate(e.target.value)}
          placeholder="开始日期"
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
        />
        <input
          type="date"
          value={endDate}
          onChange={e => setEndDate(e.target.value)}
          placeholder="结束日期"
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
        />
        <input
          type="number"
          value={capital}
          onChange={e => setCapital(e.target.value)}
          placeholder="初始资金"
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)', width: '120px', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
        />
        <button onClick={handleRun} disabled={loading} className="analyze-btn" style={{ padding: '8px 20px' }}>
          {loading ? '回测中...' : '运行回测'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <>
          {/* 绩效指标 */}
          <div className="metrics-grid" style={{ marginBottom: '16px' }}>
            <div className="metric-card">
              <h3>总收益率</h3>
              <p className="price" style={{ fontSize: '20px', color: result.total_return >= 0 ? '#ef5350' : '#26a69a' }}>
                {(result.total_return * 100).toFixed(2)}%
              </p>
            </div>
            <div className="metric-card">
              <h3>年化收益</h3>
              <p className="price" style={{ fontSize: '20px' }}>
                {(result.annualized_return * 100).toFixed(2)}%
              </p>
            </div>
            <div className="metric-card">
              <h3>最大回撤</h3>
              <p className="price" style={{ fontSize: '20px', color: '#26a69a' }}>
                -{(result.max_drawdown * 100).toFixed(2)}%
              </p>
            </div>
            <div className="metric-card">
              <h3>夏普比率</h3>
              <p className="price" style={{ fontSize: '20px' }}>
                {result.sharpe_ratio.toFixed(3)}
              </p>
            </div>
            <div className="metric-card">
              <h3>胜率</h3>
              <p className="price" style={{ fontSize: '20px' }}>
                {(result.win_rate * 100).toFixed(1)}%
              </p>
            </div>
            <div className="metric-card">
              <h3>交易次数</h3>
              <p className="price" style={{ fontSize: '20px' }}>
                {result.total_trades}
              </p>
            </div>
          </div>

          {/* 权益曲线 */}
          {result.portfolio_history.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ fontSize: '14px', color: 'var(--text-primary)', margin: '8px 0' }}>权益曲线</h4>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={result.portfolio_history}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v?.slice(5) ?? ''} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v / 10000).toFixed(1)}万`} width={65} />
                  <Tooltip
                    formatter={(value: number) => [`¥${value.toLocaleString()}`, '组合市值']}
                    labelFormatter={label => `日期: ${label}`}
                  />
                  <Legend />
                  <ReferenceLine y={result.initial_capital} stroke="#999" strokeDasharray="3 3" label="初始资金" />
                  <Line type="monotone" dataKey="portfolio_value" name="组合市值" stroke="#1a73e8" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* 交易记录 */}
          {result.trades.length > 0 && (
            <details>
              <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '14px', marginTop: '8px' }}>
                查看交易记录 ({result.trades.length} 笔)
              </summary>
              <div style={{ overflowX: 'auto', marginTop: '8px' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid var(--border-color)' }}>
                      <th style={{ padding: '6px 8px', textAlign: 'left' }}>日期</th>
                      <th style={{ padding: '6px 8px', textAlign: 'center' }}>操作</th>
                      <th style={{ padding: '6px 8px', textAlign: 'right' }}>股数</th>
                      <th style={{ padding: '6px 8px', textAlign: 'right' }}>价格</th>
                      <th style={{ padding: '6px 8px', textAlign: 'right' }}>盈亏</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.trades.map((t, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '6px 8px' }}>{t.date}</td>
                        <td style={{ padding: '6px 8px', textAlign: 'center', color: t.action === 'BUY' ? '#ef5350' : '#26a69a', fontWeight: 'bold' }}>
                          {t.action === 'BUY' ? '买入' : '卖出'}
                        </td>
                        <td style={{ padding: '6px 8px', textAlign: 'right' }}>{t.shares}</td>
                        <td style={{ padding: '6px 8px', textAlign: 'right' }}>{t.price.toFixed(2)}</td>
                        <td style={{ padding: '6px 8px', textAlign: 'right', color: (t.profit ?? 0) >= 0 ? '#ef5350' : '#26a69a' }}>
                          {t.profit != null ? `${t.profit >= 0 ? '+' : ''}${t.profit.toFixed(2)}` : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
};

export default BacktestPanel;
