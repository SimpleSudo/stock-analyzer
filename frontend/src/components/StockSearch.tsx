import React from 'react';

interface StockSearchProps {
  onSelect: (symbol: string) => void;
  popularStocks: Array<{ symbol: string; name: string }>;
}

const StockSearch: React.FC<StockSearchProps> = ({ onSelect, popularStocks }) => {
  const [input, setInput] = React.useState('');
  const [filtered, setFiltered] = React.useState<Array<{ symbol: string; name: string }>>([]);

  React.useEffect(() => {
    if (!input) {
      setFiltered([]);
      return;
    }
    const lower = input.toLowerCase();
    const results = popularStocks.filter(
      stock =>
        stock.symbol.toLowerCase().includes(lower) ||
        stock.name.toLowerCase().includes(lower)
    );
    setFiltered(results.slice(0, 10));
  }, [input, popularStocks]);

  const handleSelect = (stock: { symbol: string; name: string }) => {
    setInput(stock.symbol);
    setFiltered([]);
    onSelect(stock.symbol);
  };

  return (
    <div style={{ position: 'relative', width: '200px' }}>
      <input
        type="text"
        placeholder="搜索股票代码或名称"
        value={input}
        onChange={e => setInput(e.target.value)}
        style={{
          width: '100%',
          padding: '8px 12px',
          border: '1px solid #ddd',
          borderRadius: '4px',
          fontSize: '16px',
          boxSizing: 'border-box',
        }}
      />
      {filtered.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            border: '1px solid #ddd',
            borderTop: 'none',
            borderRadius: '0 0 4px 4px',
            backgroundColor: 'white',
            zIndex: 1000,
            maxHeight: '200px',
            overflowY: 'auto',
          }}
        >
          {filtered.map(stock => (
            <div
              key={stock.symbol}
              onClick={() => handleSelect(stock)}
              style={{
                padding: '8px 12px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee',
              }}
            >
              <strong>{stock.symbol}</strong> - {stock.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockSearch;
