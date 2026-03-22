import React from 'react';
import type { CapitalFlow } from '../utils/types';
import {
  ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell, Legend,
} from 'recharts';

interface Props {
  capitalFlow: CapitalFlow;
}

const fmt万 = (n: number) => {
  const abs = Math.abs(n);
  if (abs >= 10000) return `${(n / 10000).toFixed(1)}亿`;
  return `${n.toFixed(0)}万`;
};

/** 趋势标签颜色 */
const trendColor = (trend: string): string => {
  if (trend.includes('流入')) return '#26a69a';
  if (trend.includes('流出')) return '#ef5350';
  return '#ff9800';
};

/** 博弈态势颜色 */
const retailColor = (desc: string): string => {
  if (desc.includes('主力流入')) return '#26a69a';
  if (desc.includes('主力流出')) return '#ef5350';
  return '#ff9800';
};

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--bg-primary, #fff)',
      border: '1px solid var(--border-color, #ddd)',
      borderRadius: '6px', padding: '10px 12px', fontSize: '12px',
    }}>
      <p style={{ margin: '0 0 6px', fontWeight: 600 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} style={{ margin: '2px 0', color: p.color }}>
          {p.name === 'main_net' ? '主力净流入' : p.name === 'cumulative' ? '累计净流入' : p.name}：
          {fmt万(p.value)}
        </p>
      ))}
    </div>
  );
};

const CapitalFlowChart: React.FC<Props> = ({ capitalFlow }) => {
  // 计算累计净流入（用于折线）
  let cum = 0;
  const chartData = capitalFlow.history.map(item => {
    cum += item.main_net;
    return { ...item, cumulative: parseFloat(cum.toFixed(2)) };
  });

  const tc = trendColor(capitalFlow.main_trend);
  const rc = retailColor(capitalFlow.retail_vs_main);

  return (
    <div className="metric-card" style={{ gridColumn: '1 / -1', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ margin: 0, fontSize: '16px' }}>💰 主力资金流向</h3>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{
            padding: '3px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600,
            background: `${tc}22`, color: tc,
          }}>
            {capitalFlow.main_trend}
          </span>
          <span style={{
            padding: '3px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600,
            background: `${rc}22`, color: rc,
          }}>
            {capitalFlow.retail_vs_main}
          </span>
        </div>
      </div>

      {/* 汇总数字 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '16px' }}>
        {[
          { label: '今日净流入', val: capitalFlow.today_main_net },
          { label: '5日净流入', val: capitalFlow.five_day_main_net },
          { label: '10日净流入', val: capitalFlow.ten_day_main_net },
        ].map(({ label, val }) => (
          <div key={label} style={{
            textAlign: 'center', padding: '8px',
            background: 'var(--bg-secondary, #f5f5f5)', borderRadius: '6px',
          }}>
            <p style={{ fontSize: '11px', color: 'var(--text-secondary, #888)', margin: 0 }}>{label}</p>
            <p style={{
              fontSize: '14px', fontWeight: 700, margin: '3px 0 0',
              color: val >= 0 ? '#ef5350' : '#26a69a',
            }}>
              {val >= 0 ? '+' : ''}{fmt万(val)}
            </p>
          </div>
        ))}
      </div>

      {/* 柱状图 + 折线 */}
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color, #eee)" />
          <XAxis
            dataKey="date"
            tickFormatter={(v: string) => v.slice(5)}  // 只显示月-日
            tick={{ fontSize: 11 }}
          />
          <YAxis
            yAxisId="left"
            tickFormatter={fmt万}
            tick={{ fontSize: 11 }}
            width={55}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={fmt万}
            tick={{ fontSize: 11 }}
            width={55}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine yAxisId="left" y={0} stroke="var(--border-color, #ccc)" />
          <Bar yAxisId="left" dataKey="main_net" name="main_net" radius={[2, 2, 0, 0]}>
            {chartData.map((entry, idx) => (
              <Cell key={idx} fill={entry.main_net >= 0 ? '#ef5350' : '#26a69a'} />
            ))}
          </Bar>
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="cumulative"
            stroke="#1a73e8"
            dot={false}
            strokeWidth={2}
            name="cumulative"
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p style={{ fontSize: '11px', color: 'var(--text-secondary, #888)', margin: '6px 0 0', textAlign: 'center' }}>
        柱形：每日主力净流入（红=净流入 / 绿=净流出）｜折线：累计净流入
      </p>
    </div>
  );
};

export default CapitalFlowChart;
