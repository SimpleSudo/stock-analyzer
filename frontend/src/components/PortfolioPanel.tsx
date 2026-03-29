import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { analyzePortfolio } from '../services/api';
import type { PortfolioResult } from '../utils/types';

const COLORS = ['#1a73e8', '#ef5350', '#26a69a', '#ff9800', '#9c27b0', '#e91e63', '#00bcd4', '#795548', '#607d8b', '#4caf50'];

const PortfolioPanel: React.FC = () => {
  const [input, setInput] = useState('');
  const [result, setResult] = useState<PortfolioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    const symbols = input.split(/[,，\s]+/).filter(Boolean);
    if (symbols.length < 2) {
      setError('请输入至少2只股票代码（逗号分隔）');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await analyzePortfolio(symbols);
      if (res.error) setError(res.error);
      else setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '分析失败');
    }
    setLoading(false);
  };

  return (
    <div style={{ marginTop: '16px' }}>
      <h3 style={{ margin: '0 0 12px', fontSize: '16px', color: 'var(--text-primary)' }}>📈 组合分析</h3>

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px', flexWrap: 'wrap' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="输入股票代码，逗号分隔（如 000001,600036,600519）"
          style={{ flex: 1, minWidth: '240px', padding: '8px 12px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
        />
        <button onClick={handleAnalyze} disabled={loading} className="analyze-btn" style={{ padding: '8px 20px' }}>
          {loading ? '分析中...' : '组合分析'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {result && (
        <>
          {/* 等权组合统计 */}
          <div className="metrics-grid" style={{ marginBottom: '16px' }}>
            <div className="metric-card">
              <h3>等权总收益</h3>
              <p className="price" style={{ fontSize: '20px', color: result.equal_weight_portfolio.total_return >= 0 ? '#ef5350' : '#26a69a' }}>
                {result.equal_weight_portfolio.total_return.toFixed(2)}%
              </p>
            </div>
            <div className="metric-card">
              <h3>年化收益</h3>
              <p className="price" style={{ fontSize: '20px' }}>{result.equal_weight_portfolio.annualized_return.toFixed(2)}%</p>
            </div>
            <div className="metric-card">
              <h3>年化波动率</h3>
              <p className="price" style={{ fontSize: '20px' }}>{result.equal_weight_portfolio.annualized_volatility.toFixed(2)}%</p>
            </div>
            <div className="metric-card">
              <h3>夏普比率</h3>
              <p className="price" style={{ fontSize: '20px' }}>{result.equal_weight_portfolio.sharpe_ratio.toFixed(3)}</p>
            </div>
          </div>

          {/* 收益曲线 */}
          {result.return_curves.length > 0 && (
            <div style={{ marginBottom: '16px' }}>
              <h4 style={{ fontSize: '14px', margin: '8px 0' }}>归一化收益曲线（基准=100）</h4>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={result.return_curves}>
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v?.slice(5) ?? ''} interval="preserveStartEnd" />
                  <YAxis tick={{ fontSize: 10 }} width={50} />
                  <Tooltip />
                  <Legend />
                  {result.symbols.map((sym, i) => (
                    <Line key={sym} type="monotone" dataKey={sym} stroke={COLORS[i % COLORS.length]} strokeWidth={1.5} dot={false} name={sym} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* 相关性矩阵 */}
          {result.correlation && (
            <details style={{ marginTop: '12px' }}>
              <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '14px' }}>查看相关性矩阵</summary>
              <div style={{ overflowX: 'auto', marginTop: '8px' }}>
                <table style={{ borderCollapse: 'collapse', fontSize: '12px' }}>
                  <thead>
                    <tr>
                      <th style={{ padding: '4px 8px' }}></th>
                      {result.symbols.map(s => <th key={s} style={{ padding: '4px 8px' }}>{s}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {result.symbols.map(s1 => (
                      <tr key={s1}>
                        <td style={{ padding: '4px 8px', fontWeight: 'bold' }}>{s1}</td>
                        {result.symbols.map(s2 => {
                          const val = result.correlation[s1]?.[s2] ?? 0;
                          const bg = val > 0.7 ? '#ef535033' : val < 0.3 ? '#26a69a33' : 'transparent';
                          return (
                            <td key={s2} style={{ padding: '4px 8px', textAlign: 'center', background: bg }}>
                              {val.toFixed(3)}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}

          {/* 个股统计 */}
          {result.individual_stats && (
            <details style={{ marginTop: '12px' }}>
              <summary style={{ cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '14px' }}>查看个股统计</summary>
              <div className="metrics-grid" style={{ marginTop: '8px' }}>
                {Object.entries(result.individual_stats).map(([sym, stats]: [string, any]) => (
                  <div key={sym} className="metric-card" style={{ textAlign: 'left', padding: '12px' }}>
                    <h3 style={{ textAlign: 'center' }}>{sym}</h3>
                    <p style={{ fontSize: '12px', margin: '4px 0' }}>年化收益: {stats.annualized_return}%</p>
                    <p style={{ fontSize: '12px', margin: '4px 0' }}>年化波动: {stats.annualized_volatility}%</p>
                    <p style={{ fontSize: '12px', margin: '4px 0' }}>夏普比率: {stats.sharpe_ratio}</p>
                    <p style={{ fontSize: '12px', margin: '4px 0' }}>最大回撤: -{stats.max_drawdown}%</p>
                  </div>
                ))}
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
};

export default PortfolioPanel;
