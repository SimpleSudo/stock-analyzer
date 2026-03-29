import React, { useEffect, useState, useCallback } from 'react';
import { getWatchlist, addToWatchlist, removeFromWatchlist } from '../services/api';
import type { WatchlistItem } from '../utils/types';

interface Props {
  currentSymbol?: string;
  currentName?: string;
  onSelect: (symbol: string) => void;
}

const WatchlistPanel: React.FC<Props> = ({ currentSymbol, currentName, onSelect }) => {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const data = await getWatchlist();
      setItems(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleAdd = async () => {
    if (!currentSymbol) return;
    setLoading(true);
    try {
      await addToWatchlist(currentSymbol, currentName);
      await refresh();
    } catch { /* ignore */ }
    setLoading(false);
  };

  const handleRemove = async (symbol: string) => {
    try {
      await removeFromWatchlist(symbol);
      await refresh();
    } catch { /* ignore */ }
  };

  const isInWatchlist = items.some(i => i.symbol === currentSymbol);

  return (
    <div className="watchlist-panel" style={{ marginTop: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--text-primary)' }}>⭐ 自选股</h3>
        {currentSymbol && !isInWatchlist && (
          <button onClick={handleAdd} disabled={loading}
            style={{ padding: '4px 12px', fontSize: '12px', background: '#1a73e8', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
            + 加入自选
          </button>
        )}
        {currentSymbol && isInWatchlist && (
          <span style={{ fontSize: '12px', color: '#26a69a' }}>已在自选</span>
        )}
      </div>

      {items.length === 0 ? (
        <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>暂无自选股</p>
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {items.map(item => (
            <div key={item.symbol}
              style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                background: 'var(--bg-secondary)', border: '1px solid var(--border-color)',
                borderRadius: '6px', padding: '6px 10px', fontSize: '13px',
              }}>
              <span
                style={{ cursor: 'pointer', color: '#1a73e8' }}
                onClick={() => onSelect(item.symbol)}
                title="点击分析"
              >
                {item.name || item.symbol}
              </span>
              <span style={{ color: 'var(--text-secondary)', fontSize: '11px' }}>({item.symbol})</span>
              <button
                onClick={() => handleRemove(item.symbol)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#999', fontSize: '14px', padding: '0 2px' }}
                title="移除"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WatchlistPanel;
