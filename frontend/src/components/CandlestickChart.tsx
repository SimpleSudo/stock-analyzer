import React, { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { ChartPointWithIndicators } from '../utils/types';

interface CandlestickChartProps {
  data: ChartPointWithIndicators[];
}

/**
 * 自定义蜡烛 Shape - 绘制真实 K 线（含实体 + 影线）
 * A 股配色：涨红跌绿
 */
const CandleShape = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const { open, close, high, low } = payload;
  if (open == null || close == null || high == null || low == null) return null;

  const isUp = close >= open;
  const color = isUp ? '#ef5350' : '#26a69a'; // 涨红跌绿（A 股惯例）

  // 坐标系换算：recharts 的 y 是从顶部往下的屏幕坐标
  // 需要将价格映射到屏幕坐标
  const yScale = props.yAxis?.scale;
  if (!yScale) return null;

  const yHigh   = yScale(high);
  const yLow    = yScale(low);
  const yOpen   = yScale(open);
  const yClose  = yScale(close);
  const yBodyTop    = Math.min(yOpen, yClose);
  const yBodyBottom = Math.max(yOpen, yClose);
  const bodyHeight  = Math.max(yBodyBottom - yBodyTop, 1); // 最少 1px
  const centerX     = x + width / 2;
  const candleWidth = Math.max(width - 2, 2);

  return (
    <g>
      {/* 上影线 */}
      <line
        x1={centerX} y1={yHigh}
        x2={centerX} y2={yBodyTop}
        stroke={color} strokeWidth={1}
      />
      {/* 下影线 */}
      <line
        x1={centerX} y1={yBodyBottom}
        x2={centerX} y2={yLow}
        stroke={color} strokeWidth={1}
      />
      {/* K 线实体：涨为实心红，跌为实心绿 */}
      <rect
        x={centerX - candleWidth / 2}
        y={yBodyTop}
        width={candleWidth}
        height={bodyHeight}
        fill={isUp ? color : 'transparent'}
        stroke={color}
        strokeWidth={1}
      />
    </g>
  );
};

/**
 * 自定义 Tooltip
 */
const CandleTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;

  const isUp = d.close >= d.open;
  const color = isUp ? '#ef5350' : '#26a69a';

  return (
    <div style={{
      background: 'var(--bg-primary, #fff)',
      border: '1px solid var(--border-color, #ddd)',
      borderRadius: '6px',
      padding: '10px 14px',
      fontSize: '13px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      color: 'var(--text-primary, #333)',
    }}>
      <p style={{ margin: '0 0 6px', fontWeight: 'bold' }}>{label}</p>
      <p style={{ margin: '2px 0', color: '#666' }}>开盘：<span style={{ color }}>{d.open?.toFixed(2)}</span></p>
      <p style={{ margin: '2px 0', color: '#666' }}>最高：<span style={{ color: '#ef5350' }}>{d.high?.toFixed(2)}</span></p>
      <p style={{ margin: '2px 0', color: '#666' }}>最低：<span style={{ color: '#26a69a' }}>{d.low?.toFixed(2)}</span></p>
      <p style={{ margin: '2px 0', color: '#666' }}>收盘：<span style={{ color }}>{d.close?.toFixed(2)}</span></p>
      <p style={{ margin: '2px 0', color: '#666' }}>成交量：<span>{d.volume?.toLocaleString()}</span></p>
      {d.ma5  != null && <p style={{ margin: '2px 0', color: '#2196f3' }}>MA5：{d.ma5.toFixed(2)}</p>}
      {d.ma10 != null && <p style={{ margin: '2px 0', color: '#ff9800' }}>MA10：{d.ma10.toFixed(2)}</p>}
      {d.ma20 != null && <p style={{ margin: '2px 0', color: '#9c27b0' }}>MA20：{d.ma20.toFixed(2)}</p>}
      {d.ma60 != null && <p style={{ margin: '2px 0', color: '#f44336' }}>MA60：{d.ma60.toFixed(2)}</p>}
    </div>
  );
};

const CandlestickChart: React.FC<CandlestickChartProps> = ({ data }) => {
  // 计算价格区间，给上下留一点空白
  const { yMin, yMax } = useMemo(() => {
    if (!data.length) return { yMin: 0, yMax: 100 };
    let mn = Infinity, mx = -Infinity;
    for (const d of data) {
      if (d.low  != null) mn = Math.min(mn, d.low);
      if (d.high != null) mx = Math.max(mx, d.high);
    }
    const padding = (mx - mn) * 0.05;
    return { yMin: mn - padding, yMax: mx + padding };
  }, [data]);

  // 检查哪些均线有有效数据
  const hasMa5  = data.some(d => d.ma5  != null);
  const hasMa10 = data.some(d => d.ma10 != null);
  const hasMa20 = data.some(d => d.ma20 != null);
  const hasMa60 = data.some(d => d.ma60 != null);

  if (!data.length) {
    return (
      <div style={{ textAlign: 'center', padding: '40px', color: '#999' }}>
        暂无 K 线数据
      </div>
    );
  }

  return (
    <div style={{ width: '100%' }}>
      <h4 style={{ margin: '16px 0 4px', fontSize: '14px', color: 'var(--text-primary, #333)' }}>
        📈 K 线图（含均线）
      </h4>
      <ResponsiveContainer width="100%" height={380}>
        <ComposedChart
          data={data}
          margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
        >
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10 }}
            tickFormatter={v => v?.slice(5) ?? ''}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[yMin, yMax]}
            tick={{ fontSize: 10 }}
            tickFormatter={v => v.toFixed(2)}
            width={60}
          />
          <Tooltip content={<CandleTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px' }}
            formatter={(value) => <span style={{ color: 'var(--text-primary, #555)' }}>{value}</span>}
          />

          {/* 真正的 K 线柱（使用自定义 CandleShape） */}
          <Bar
            dataKey="close"
            name="K线"
            shape={<CandleShape />}
            legendType="none"
            isAnimationActive={false}
          />

          {/* 均线（各使用独立 dataKey） */}
          {hasMa5 && (
            <Line type="monotone" dataKey="ma5"  stroke="#2196f3" strokeWidth={1.5} dot={false} name="MA5"  connectNulls />
          )}
          {hasMa10 && (
            <Line type="monotone" dataKey="ma10" stroke="#ff9800" strokeWidth={1.5} dot={false} name="MA10" connectNulls />
          )}
          {hasMa20 && (
            <Line type="monotone" dataKey="ma20" stroke="#9c27b0" strokeWidth={1.5} dot={false} name="MA20" connectNulls />
          )}
          {hasMa60 && (
            <Line type="monotone" dataKey="ma60" stroke="#f44336" strokeWidth={1.5} dot={false} name="MA60" connectNulls />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CandlestickChart;
