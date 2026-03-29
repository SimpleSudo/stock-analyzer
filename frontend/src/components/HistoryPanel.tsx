import React, { useEffect, useState, useCallback } from 'react';
import { getHistory } from '../services/api';
import type { HistoryRecord } from '../utils/types';

interface Props {
  onSelect: (symbol: string) => void;
}

const signalColor = (signal: string) => {
  if (signal.includes('买入')) return '#ef5350';
  if (signal.includes('卖出')) return '#26a69a';
  return '#999';
};

const HistoryPanel: React.FC<Props> = ({ onSelect }) => {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getHistory(undefined, 30);
      setRecords(data);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  if (loading && records.length === 0) {
    return <p style={{ color: '#999', fontSize: '13px', padding: '12px 0' }}>加载中...</p>;
  }

  if (records.length === 0) {
    return <p style={{ color: '#999', fontSize: '13px', padding: '12px 0' }}>暂无分析记录</p>;
  }

  return (
    <div className="history-panel" style={{ marginTop: '16px' }}>
      <h3 style={{ margin: '0 0 12px', fontSize: '16px', color: 'var(--text-primary)' }}>📜 分析历史</h3>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border-color)' }}>
              <th style={{ padding: '6px 8px', textAlign: 'left' }}>时间</th>
              <th style={{ padding: '6px 8px', textAlign: 'left' }}>股票</th>
              <th style={{ padding: '6px 8px', textAlign: 'center' }}>信号</th>
              <th style={{ padding: '6px 8px', textAlign: 'right' }}>评分</th>
              <th style={{ padding: '6px 8px', textAlign: 'right' }}>价格</th>
            </tr>
          </thead>
          <tbody>
            {records.map(r => (
              <tr key={r.id} style={{ borderBottom: '1px solid var(--border-color)', cursor: 'pointer' }}
                onClick={() => onSelect(r.symbol)} title="点击重新分析">
                <td style={{ padding: '6px 8px', color: 'var(--text-secondary)', fontSize: '12px' }}>
                  {r.created_at?.slice(0, 16).replace('T', ' ')}
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <span style={{ color: '#1a73e8' }}>{r.name}</span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '11px', marginLeft: '4px' }}>({r.symbol})</span>
                </td>
                <td style={{ padding: '6px 8px', textAlign: 'center', color: signalColor(r.signal), fontWeight: 'bold' }}>
                  {r.signal}
                </td>
                <td style={{ padding: '6px 8px', textAlign: 'right', color: r.score > 0 ? '#ef5350' : r.score < 0 ? '#26a69a' : '#999' }}>
                  {r.score > 0 ? `+${r.score}` : r.score}
                </td>
                <td style={{ padding: '6px 8px', textAlign: 'right' }}>
                  {r.price?.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HistoryPanel;
