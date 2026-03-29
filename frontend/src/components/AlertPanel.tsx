import React, { useEffect, useState, useCallback } from 'react';
import { getAlerts, createAlert, deleteAlert } from '../services/api';
import type { AlertItem } from '../utils/types';

interface Props {
  symbol?: string;
}

const AlertPanel: React.FC<Props> = ({ symbol }) => {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [price, setPrice] = useState('');
  const [direction, setDirection] = useState<'above' | 'below'>('above');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getAlerts();
      setAlerts(data);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleCreate = async () => {
    if (!symbol || !price) return;
    setLoading(true);
    try {
      await createAlert(symbol, Number(price), direction, note || undefined);
      setPrice('');
      setNote('');
      await refresh();
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteAlert(id);
      await refresh();
    } catch { /* ignore */ }
  };

  return (
    <div style={{ marginTop: '16px' }}>
      <h3 style={{ margin: '0 0 12px', fontSize: '16px', color: 'var(--text-primary)' }}>🔔 价格告警</h3>

      {symbol && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            value={direction}
            onChange={e => setDirection(e.target.value as any)}
            style={{ padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
          >
            <option value="above">价格上穿</option>
            <option value="below">价格下穿</option>
          </select>
          <input
            type="number"
            value={price}
            onChange={e => setPrice(e.target.value)}
            placeholder="目标价格"
            style={{ width: '100px', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
          />
          <input
            value={note}
            onChange={e => setNote(e.target.value)}
            placeholder="备注（可选）"
            style={{ flex: 1, minWidth: '100px', padding: '6px 8px', borderRadius: '4px', border: '1px solid var(--border-color)', background: 'var(--bg-primary)', color: 'var(--text-primary)' }}
          />
          <button onClick={handleCreate} disabled={loading || !price}
            style={{ padding: '6px 14px', fontSize: '13px', background: '#1a73e8', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            设置告警
          </button>
        </div>
      )}

      {alerts.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>暂无告警</p>
      ) : (
        <div style={{ fontSize: '13px' }}>
          {alerts.map(a => (
            <div key={a.id} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 10px', borderBottom: '1px solid var(--border-color)',
            }}>
              <div>
                <span style={{ fontWeight: 'bold', color: '#1a73e8' }}>{a.symbol}</span>
                <span style={{ color: 'var(--text-secondary)', margin: '0 6px' }}>
                  {a.direction === 'above' ? '上穿' : '下穿'} {a.target_price}
                </span>
                {a.note && <span style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>({a.note})</span>}
                {a.triggered ? <span style={{ color: '#26a69a', marginLeft: '6px', fontSize: '11px' }}>已触发</span> : null}
              </div>
              <button onClick={() => handleDelete(a.id)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#999', fontSize: '16px' }}>×</button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AlertPanel;
