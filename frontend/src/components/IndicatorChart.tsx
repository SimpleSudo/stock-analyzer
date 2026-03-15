import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  Label
} from 'recharts';

interface IndicatorData {
  date: string;
  rsi?: number;
  macd?: number;
  signal?: number;
  hist?: number;
  bb_upper?: number;
  bb_mid?: number;
  bb_lower?: number;
}

interface IndicatorChartProps {
  data: IndicatorData[];
}

const IndicatorChart: React.FC<IndicatorChartProps> = ({ data }) => {
  // Filter data for indicators that exist
  const rsiData = data.filter(item => item.rsi !== undefined);
  const macdData = data.filter(item => item.macd !== undefined && item.signal !== undefined);
  const bbData = data.filter(item => item.bb_upper !== undefined);

  // RSI Tooltip
  const RSISpecificTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: '10px', 
          border: '1px solid #ccc',
          borderRadius: '4px'
        }}>
          <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: '2px 0', color: '#ff9800' }}>RSI: {payload[0].value?.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  // MACD Tooltip
  const MACDSpecificTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const macdItem = payload.find((p: any) => p.name === 'MACD');
      const signalItem = payload.find((p: any) => p.name === 'Signal');
      const histItem = payload.find((p: any) => p.name === 'Histogram');
      return (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: '10px', 
          border: '1px solid #ccc',
          borderRadius: '4px'
        }}>
          <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: '2px 0', color: '#2196f3' }}>MACD: {macdItem?.value?.toFixed(4)}</p>
          <p style={{ margin: '2px 0', color: '#ff9800' }}>Signal: {signalItem?.value?.toFixed(4)}</p>
          <p style={{ margin: '2px 0', color: histItem?.value >= 0 ? '#4caf50' : '#f44336' }}>
            Histogram: {histItem?.value?.toFixed(4)}
          </p>
        </div>
      );
    }
    return null;
  };

  // Bollinger Tooltip
  const BBSpecificTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div style={{ 
          backgroundColor: '#fff', 
          padding: '10px', 
          border: '1px solid #ccc',
          borderRadius: '4px'
        }}>
          <p style={{ margin: '0 0 5px 0', fontWeight: 'bold' }}>{label}</p>
          <p style={{ margin: '2px 0', color: '#9c27b0' }}>Upper: {payload[0]?.value?.toFixed(2)}</p>
          <p style={{ margin: '2px 0', color: '#607d8b' }}>Middle: {payload[1]?.value?.toFixed(2)}</p>
          <p style={{ margin: '2px 0', color: '#9c27b0' }}>Lower: {payload[2]?.value?.toFixed(2)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ResponsiveContainer width="100%" height={120}>
        <LineChart 
          data={rsiData}
          margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 10 }}
            tickFormatter={(value) => value.slice(5)}
          />
          <YAxis 
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
          >
            <Label value="RSI" position="insideLeft" rotate={-90} style={{ fill: '#666' }} />
          </YAxis>
          <Tooltip content={RSISpecificTooltip} />
          <Legend verticalAlign="top" height={36} />
          
          {/* RSI Line */}
          <Line 
            type="monotone" 
            dataKey="rsi" 
            stroke="#ff9800" 
            strokeWidth={2}
            dot={false}
            name="RSI"
          />
          
          {/* RSI Reference lines (30, 70) */}
          <Line 
            type="monotone" 
            dataKey="date" 
            stroke="#9e9e9e"
            strokeWidth={1}
            strokeDasharray="5 5"
            name="RSI 30"
            isAnimationActive={false}
          >
            <Label value="30" position="end" />
          </Line>
          <Line 
            type="monotone" 
            dataKey="date" 
            stroke="#9e9e9e"
            strokeWidth={1}
            strokeDasharray="5 5"
            name="RSI 70"
            isAnimationActive={false}
          >
            <Label value="70" position="end" />
          </Line>
        </LineChart>
      </ResponsiveContainer>
      
      {/* MACD Chart */}
      {macdData.length > 0 && (
        <ResponsiveContainer width="100%" height={120}>
          <LineChart 
            data={macdData}
            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10 }}
              tickFormatter={(value) => value.slice(5)}
            />
            <YAxis 
              tick={{ fontSize: 10 }}
            >
              <Label value="MACD" position="insideLeft" rotate={-90} style={{ fill: '#666' }} />
            </YAxis>
            <Tooltip content={MACDSpecificTooltip} />
            <Legend verticalAlign="top" height={36} />
            
            {/* MACD Line */}
            <Line 
              type="monotone" 
              dataKey="macd" 
              stroke="#2196f3" 
              strokeWidth={2}
              dot={false}
              name="MACD"
            />
            
            {/* Signal Line */}
            <Line 
              type="monotone" 
              dataKey="signal" 
              stroke="#ff9800" 
              strokeWidth={2}
              dot={false}
              name="Signal"
            />
            
            {/* Histogram - using a simpler approach */}
            <Line 
              type="monotone" 
              dataKey="hist" 
              stroke="#ff9800" 
              strokeWidth={2}
              dot={false}
              name="Histogram"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
      
      {/* Bollinger Bands Chart */}
      {bbData.length > 0 && (
        <ResponsiveContainer width="100%" height={120}>
          <LineChart 
            data={bbData}
            margin={{ top: 20, right: 30, left: 0, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10 }}
              tickFormatter={(value) => value.slice(5)}
            />
            <YAxis 
              tick={{ fontSize: 10 }}
            >
              <Label value="价格" position="insideLeft" rotate={-90} style={{ fill: '#666' }} />
            </YAxis>
            <Tooltip content={BBSpecificTooltip} />
            <Legend verticalAlign="top" height={36} />
            
            {/* Bollinger Bands */}
            <Line 
              type="monotone" 
              dataKey="bb_upper" 
              stroke="#9c27b0" 
              strokeWidth={1}
              dot={false}
              name="上轨"
            />
            <Line 
              type="monotone" 
              dataKey="bb_mid" 
              stroke="#607d8b" 
              strokeWidth={1}
              dot={false}
              name="中轨"
            />
            <Line 
              type="monotone" 
              dataKey="bb_lower" 
              stroke="#9c27b0" 
              strokeWidth={1}
              dot={false}
              name="下轨"
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default IndicatorChart;