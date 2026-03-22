import React from 'react';
import {
  LineChart,
  Line,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import type { ChartPointWithIndicators } from '../utils/types';

interface IndicatorChartProps {
  data: ChartPointWithIndicators[];
}

const tooltipStyle = {
  background: 'var(--bg-primary, #fff)',
  border: '1px solid var(--border-color, #ddd)',
  borderRadius: '6px',
  padding: '8px 12px',
  fontSize: '12px',
  boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
  color: 'var(--text-primary, #333)',
};

/** RSI Tooltip */
const RSITooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const rsi = payload.find((p: any) => p.dataKey === 'rsi');
  return (
    <div style={tooltipStyle}>
      <p style={{ margin: '0 0 4px', fontWeight: 'bold' }}>{label}</p>
      {rsi && <p style={{ margin: 0, color: '#ff9800' }}>RSI：{rsi.value?.toFixed(2)}</p>}
    </div>
  );
};

/** MACD Tooltip */
const MACDTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const macd   = payload.find((p: any) => p.dataKey === 'macd');
  const signal = payload.find((p: any) => p.dataKey === 'signal');
  const hist   = payload.find((p: any) => p.dataKey === 'hist');
  return (
    <div style={tooltipStyle}>
      <p style={{ margin: '0 0 4px', fontWeight: 'bold' }}>{label}</p>
      {macd   && <p style={{ margin: '2px 0', color: '#2196f3' }}>MACD：{macd.value?.toFixed(4)}</p>}
      {signal && <p style={{ margin: '2px 0', color: '#ff9800' }}>Signal：{signal.value?.toFixed(4)}</p>}
      {hist   && (
        <p style={{ margin: '2px 0', color: hist.value >= 0 ? '#ef5350' : '#26a69a' }}>
          Hist：{hist.value?.toFixed(4)}
        </p>
      )}
    </div>
  );
};

const IndicatorChart: React.FC<IndicatorChartProps> = ({ data }) => {
  const hasRSI  = data.some(d => d.rsi   != null);
  const hasMacd = data.some(d => d.macd  != null);
  const hasBB   = data.some(d => d.bb_upper != null);

  if (!data.length) return null;

  return (
    <div style={{ width: '100%', marginTop: '8px' }}>

      {/* === RSI 图 === */}
      {hasRSI && (
        <div>
          <h4 style={{ margin: '16px 0 4px', fontSize: '14px', color: 'var(--text-primary, #333)' }}>
            📊 RSI（相对强弱指标）
          </h4>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color, #eee)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                tickFormatter={v => v?.slice(5) ?? ''}
                interval="preserveStartEnd"
              />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={40} />
              <Tooltip content={<RSITooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />

              {/* RSI 超买/超卖参考线 */}
              <ReferenceLine y={70} stroke="#ef5350" strokeDasharray="4 4" label={{ value: '超买(70)', position: 'insideTopRight', fontSize: 10, fill: '#ef5350' }} />
              <ReferenceLine y={30} stroke="#26a69a" strokeDasharray="4 4" label={{ value: '超卖(30)', position: 'insideBottomRight', fontSize: 10, fill: '#26a69a' }} />
              <ReferenceLine y={50} stroke="#999" strokeDasharray="2 4" strokeWidth={0.8} />

              <Line
                type="monotone"
                dataKey="rsi"
                stroke="#ff9800"
                strokeWidth={2}
                dot={false}
                name="RSI(14)"
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* === MACD 图 === */}
      {hasMacd && (
        <div>
          <h4 style={{ margin: '16px 0 4px', fontSize: '14px', color: 'var(--text-primary, #333)' }}>
            📊 MACD
          </h4>
          <ResponsiveContainer width="100%" height={150}>
            <ComposedChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color, #eee)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                tickFormatter={v => v?.slice(5) ?? ''}
                interval="preserveStartEnd"
              />
              <YAxis tick={{ fontSize: 10 }} width={55} tickFormatter={v => v.toFixed(3)} />
              <Tooltip content={<MACDTooltip />} />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <ReferenceLine y={0} stroke="#999" strokeWidth={1} />

              {/* MACD 柱状图（涨红跌绿） */}
              <Bar
                dataKey="hist"
                name="Hist"
                fill="#ef5350"
                isAnimationActive={false}
                shape={(barProps: any) => {
                  const { x, y, width, height, value } = barProps;
                  const color = value >= 0 ? '#ef5350' : '#26a69a';
                  return <rect x={x} y={y} width={width} height={Math.abs(height)} fill={color} opacity={0.7} />;
                }}
              />

              <Line
                type="monotone"
                dataKey="macd"
                stroke="#2196f3"
                strokeWidth={2}
                dot={false}
                name="MACD"
                connectNulls
              />
              <Line
                type="monotone"
                dataKey="signal"
                stroke="#ff9800"
                strokeWidth={1.5}
                dot={false}
                name="Signal"
                connectNulls
                strokeDasharray="4 2"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* === 布林带图 === */}
      {hasBB && (
        <div>
          <h4 style={{ margin: '16px 0 4px', fontSize: '14px', color: 'var(--text-primary, #333)' }}>
            📊 布林带（Bollinger Bands）
          </h4>
          <ResponsiveContainer width="100%" height={150}>
            <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color, #eee)" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 10 }}
                tickFormatter={v => v?.slice(5) ?? ''}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={['auto', 'auto']}
                tick={{ fontSize: 10 }}
                tickFormatter={v => v.toFixed(2)}
                width={60}
              />
              <Tooltip
                formatter={(value: any, name: string) => [value?.toFixed(2), name]}
                labelStyle={{ fontWeight: 'bold' }}
              />
              <Legend wrapperStyle={{ fontSize: '12px' }} />

              <Line type="monotone" dataKey="bb_upper" stroke="#9c27b0" strokeWidth={1.5} dot={false} name="上轨" connectNulls strokeDasharray="4 2" />
              <Line type="monotone" dataKey="bb_mid"   stroke="#607d8b" strokeWidth={1.5} dot={false} name="中轨" connectNulls />
              <Line type="monotone" dataKey="close"    stroke="#333"    strokeWidth={1}   dot={false} name="收盘价" connectNulls opacity={0.4} />
              <Line type="monotone" dataKey="bb_lower" stroke="#9c27b0" strokeWidth={1.5} dot={false} name="下轨" connectNulls strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default IndicatorChart;
