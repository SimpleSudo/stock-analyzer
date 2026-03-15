import React from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

interface ChartData {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface CandlestickChartProps {
  data: ChartData[];
  ma5?: number | null;
  ma10?: number | null;
  ma20?: number | null;
  ma60?: number | null;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({ 
  data, 
  ma5, 
  ma10, 
  ma20, 
  ma60 
}) => {
  // Transform data for candlestick visualization
  const transformedData = data.map(item => ({
    ...item,
    // Candle body
    bodyTop: Math.max(item.open, item.close),
    bodyBottom: Math.min(item.open, item.close),
    bodyHeight: Math.abs(item.close - item.open),
    // Color based on price movement
    color: item.close >= item.open ? '#26a69a' : '#ef5350',
    // Wick coordinates
    wickHigh: item.high,
    wickLow: item.low,
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: '10px', 
          border: '1px solid #ccc',
          borderRadius: '4px'
        }}>
          <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: '2px 0', color: '#26a69a' }}>Open: {data.open.toFixed(2)}</p>
          <p style={{ margin: '2px 0', color: '#ef5350' }}>High: {data.high.toFixed(2)}</p>
          <p style={{ margin: '2px 0', color: '#666' }}>Low: {data.low.toFixed(2)}</p>
          <p style={{ margin: '2px 0', color: data.close >= data.open ? '#26a69a' : '#ef5350' }}>
            Close: {data.close.toFixed(2)}
          </p>
          <p style={{ margin: '2px 0' }}>Volume: {data.volume.toLocaleString()}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: '400px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={transformedData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 10 }}
            tickFormatter={(value) => value.slice(5)} // Show MM-DD only
          />
          <YAxis 
            domain={['auto', 'auto']}
            tick={{ fontSize: 10 }}
            tickFormatter={(value) => value.toFixed(2)}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Candlestick bars - using Bar for simplicity */}
          <Bar 
            dataKey="bodyHeight" 
            fill="#26a69a" 
            name="Candle"
            barSize={8}
          />
          
          {/* Moving averages */}
          {ma5 && (
            <Line 
              type="monotone" 
              dataKey="close" 
              stroke="#2196f3" 
              strokeWidth={2}
              dot={false}
              name="MA5"
            />
          )}
          
          {ma10 && (
            <Line 
              type="monotone" 
              dataKey="close" 
              stroke="#ff9800" 
              strokeWidth={2}
              dot={false}
              name="MA10"
            />
          )}
          
          {ma20 && (
            <Line 
              type="monotone" 
              dataKey="close" 
              stroke="#9c27b0" 
              strokeWidth={2}
              dot={false}
              name="MA20"
            />
          )}
          
          {ma60 && (
            <Line 
              type="monotone" 
              dataKey="close" 
              stroke="#f44336" 
              strokeWidth={2}
              dot={false}
              name="MA60"
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CandlestickChart;
