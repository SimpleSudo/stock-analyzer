import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

interface StockItem {
  code: string;
  name: string;
}

interface StockSearchProps {
  value: string;
  onChange: (value: string) => void;
  onSelect: (symbol: string) => void;
  popularStocks?: Array<{ symbol: string; name: string }>; // 保留兼容，不再使用
  placeholder?: string;
}

/**
 * 受控股票搜索组件 - 带后端实时搜索下拉补全
 * 支持输入股票代码（000001）或名称（平安银行、农产品）
 */
const StockSearch: React.FC<StockSearchProps> = ({
  value,
  onChange,
  onSelect,
  placeholder = '输入代码或名称（如：农产品）',
}) => {
  const [suggestions, setSuggestions] = useState<StockItem[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!value.trim()) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    // 防抖：300ms 后再请求
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await axios.get<{ results: StockItem[] }>('/api/search', {
          params: { q: value.trim() },
        });
        const results = res.data.results || [];
        setSuggestions(results);
        setShowDropdown(results.length > 0);
      } catch {
        setSuggestions([]);
        setShowDropdown(false);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value]);

  const handleSelect = (stock: StockItem) => {
    onChange(stock.code);
    onSelect(stock.code);
    setShowDropdown(false);
    setSuggestions([]);
  };

  const handleBlur = () => {
    // 延迟关闭，允许点击事件先触发
    setTimeout(() => setShowDropdown(false), 150);
  };

  return (
    <div style={{ position: 'relative', width: '220px' }}>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => value.trim() && setShowDropdown(suggestions.length > 0)}
        onBlur={handleBlur}
        className="stock-input"
        style={{
          width: '100%',
          padding: '10px 12px',
          border: '1px solid var(--border-color, #ddd)',
          borderRadius: '4px',
          fontSize: '15px',
          boxSizing: 'border-box',
          background: 'var(--bg-primary, #fff)',
          color: 'var(--text-primary, #333)',
        }}
      />

      {/* 加载指示 */}
      {loading && (
        <div style={{
          position: 'absolute',
          right: '10px',
          top: '50%',
          transform: 'translateY(-50%)',
          fontSize: '12px',
          color: '#999',
        }}>
          ···
        </div>
      )}

      {showDropdown && suggestions.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            border: '1px solid var(--border-color, #ddd)',
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            background: 'var(--bg-primary, #fff)',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 1000,
            maxHeight: '220px',
            overflowY: 'auto',
          }}
        >
          {suggestions.map(stock => (
            <div
              key={stock.code}
              onMouseDown={() => handleSelect(stock)}
              style={{
                padding: '9px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid var(--border-color, #eee)',
                color: 'var(--text-primary, #333)',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-secondary, #f5f5f5)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              <strong style={{ color: '#1a73e8' }}>{stock.code}</strong>
              <span style={{ marginLeft: '8px' }}>{stock.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockSearch;
