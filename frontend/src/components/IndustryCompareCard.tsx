import React from 'react';
import type { IndustryComparison, Fundamental } from '../utils/types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';

interface Props {
  industry: IndustryComparison;
  fundamental?: Fundamental;
}

const fmt = (n: number | null | undefined, decimals = 1) =>
  n != null ? n.toFixed(decimals) : 'N/A';

/** 估值结论对应的色和 Emoji */
const verdictStyle = (verdict: string): { color: string; icon: string } => {
  if (verdict.includes('偏低')) return { color: '#26a69a', icon: '✅' };
  if (verdict.includes('偏高')) return { color: '#ef5350', icon: '⚠️' };
  return { color: '#ff9800', icon: '➖' };
};

interface CompareRowProps {
  label: string;
  stockVal: number | null;
  medianVal: number | null;
  percentile: number | null;
  unit?: string;
  lowerIsBetter?: boolean;
}

const CompareRow: React.FC<CompareRowProps> = ({
  label, stockVal, medianVal, percentile, unit = '', lowerIsBetter = false,
}) => {
  if (stockVal == null && medianVal == null) return null;

  const max = Math.max(stockVal ?? 0, medianVal ?? 0) * 1.3 || 10;
  const stockColor = stockVal != null && medianVal != null
    ? (lowerIsBetter
        ? (stockVal < medianVal ? '#26a69a' : '#ef5350')
        : (stockVal > medianVal ? '#26a69a' : '#ef5350'))
    : '#1a73e8';

  const data = [
    { name: '本股', value: stockVal ?? 0, fill: stockColor },
    { name: '行业中位', value: medianVal ?? 0, fill: '#9e9e9e' },
  ];

  return (
    <div style={{ marginBottom: '14px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '4px' }}>
        <span style={{ fontSize: '13px', fontWeight: 600 }}>{label}</span>
        <span style={{ fontSize: '12px', color: 'var(--text-secondary, #888)' }}>
          {percentile != null ? `低于行业 ${percentile}% 同行` : ''}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={50}>
        <BarChart data={data} layout="vertical" margin={{ left: 60, right: 40, top: 0, bottom: 0 }}>
          <XAxis type="number" domain={[0, max]} hide />
          <YAxis type="category" dataKey="name" width={60} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(val: number) => [`${val.toFixed(2)}${unit}`, label]}
            contentStyle={{ fontSize: '12px' }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={14}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary, #666)' }}>
        <span style={{ color: stockColor, fontWeight: 600 }}>本股: {fmt(stockVal)}{unit}</span>
        <span>行业中位: {fmt(medianVal)}{unit}</span>
      </div>
    </div>
  );
};

const IndustryCompareCard: React.FC<Props> = ({ industry, fundamental }) => {
  const { color, icon } = verdictStyle(industry.valuation_verdict);

  return (
    <div className="metric-card" style={{ gridColumn: '1 / -1', padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '16px' }}>🏭 行业对比</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '13px', color: 'var(--text-secondary, #888)' }}>
            {industry.industry_name} · {industry.peer_count} 家同行
          </span>
          <span style={{
            padding: '3px 10px', borderRadius: '12px', fontSize: '12px', fontWeight: 600,
            background: `${color}22`, color,
          }}>
            {icon} {industry.valuation_verdict}
          </span>
        </div>
      </div>

      <CompareRow
        label="PE(TTM)"
        stockVal={industry.stock_pe}
        medianVal={industry.industry_median_pe}
        percentile={industry.pe_percentile}
        lowerIsBetter={true}
      />
      <CompareRow
        label="PB"
        stockVal={industry.stock_pb}
        medianVal={industry.industry_median_pb}
        percentile={industry.pb_percentile}
        lowerIsBetter={true}
      />
      {fundamental?.roe != null && (
        <CompareRow
          label="ROE"
          stockVal={fundamental.roe}
          medianVal={industry.industry_median_roe}
          percentile={null}
          unit="%"
          lowerIsBetter={false}
        />
      )}

      {/* 基本面补充数据 */}
      {fundamental && (
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '8px', marginTop: '12px',
          padding: '10px', background: 'var(--bg-secondary, #f5f5f5)', borderRadius: '6px',
        }}>
          {fundamental.roe != null && (
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary, #888)', margin: 0 }}>ROE</p>
              <p style={{ fontSize: '14px', fontWeight: 700, margin: '2px 0 0', color: fundamental.roe > 15 ? '#26a69a' : 'var(--text-primary, #333)' }}>
                {fmt(fundamental.roe)}%
              </p>
            </div>
          )}
          {fundamental.debt_ratio != null && (
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary, #888)', margin: 0 }}>资产负债率</p>
              <p style={{ fontSize: '14px', fontWeight: 700, margin: '2px 0 0', color: fundamental.debt_ratio > 70 ? '#ef5350' : 'var(--text-primary, #333)' }}>
                {fmt(fundamental.debt_ratio)}%
              </p>
            </div>
          )}
          {fundamental.gross_margin != null && (
            <div style={{ textAlign: 'center' }}>
              <p style={{ fontSize: '11px', color: 'var(--text-secondary, #888)', margin: 0 }}>毛利率</p>
              <p style={{ fontSize: '14px', fontWeight: 700, margin: '2px 0 0', color: fundamental.gross_margin > 30 ? '#26a69a' : 'var(--text-primary, #333)' }}>
                {fmt(fundamental.gross_margin)}%
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default IndustryCompareCard;
