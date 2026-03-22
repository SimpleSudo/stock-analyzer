import React, { useState } from 'react';
import type { PriceTargets, PriceTimeframe } from '../utils/types';

interface Props {
  priceTargets: PriceTargets;
}

type Tab = 'short' | 'medium' | 'long';

const TAB_CONFIG: { key: Tab; label: string; color: string }[] = [
  { key: 'short',  label: '短线 1-2周', color: '#ef5350' },
  { key: 'medium', label: '中线 1-3月', color: '#ff9800' },
  { key: 'long',   label: '长线 6-12月', color: '#26a69a' },
];

/** 将数字格式化为带两位小数的字符串 */
const fmt = (n: number | null | undefined) =>
  n != null ? n.toFixed(2) : 'N/A';

/** 盈亏比徽章色 */
const rrColor = (rr: number) =>
  rr >= 3 ? '#26a69a' : rr >= 2 ? '#ff9800' : '#ef5350';

interface PriceBarProps {
  stopLoss: number;
  buyLow: number;
  buyHigh: number;
  current: number;
  t1: number;
  t2: number;
  t3: number;
}

const PriceBar: React.FC<PriceBarProps> = ({ stopLoss, buyLow, buyHigh, current, t1, t2, t3 }) => {
  const prices = [stopLoss, buyLow, buyHigh, current, t1, t2, t3].filter(p => p > 0);
  const minP = Math.min(...prices);
  const maxP = Math.max(...prices);
  const range = maxP - minP || 1;

  const pct = (p: number) => `${((p - minP) / range * 100).toFixed(1)}%`;

  const markers: { price: number; label: string; color: string; size: number }[] = [
    { price: stopLoss, label: '止损',   color: '#ef5350',  size: 8 },
    { price: buyLow,   label: '买入↓',  color: '#66bb6a',  size: 8 },
    { price: buyHigh,  label: '买入↑',  color: '#66bb6a',  size: 8 },
    { price: current,  label: '现价',   color: '#1a73e8',  size: 12 },
    { price: t1,       label: '目标1',  color: '#ff9800',  size: 8 },
    { price: t2,       label: '目标2',  color: '#ffa726',  size: 8 },
    { price: t3,       label: '目标3',  color: '#ffcc02',  size: 8 },
  ];

  return (
    <div style={{ position: 'relative', height: '60px', margin: '16px 0 8px' }}>
      {/* 轴线 */}
      <div style={{
        position: 'absolute', top: '50%', left: 0, right: 0,
        height: '2px', background: 'var(--border-color, #ddd)',
        transform: 'translateY(-50%)',
      }} />
      {/* 买入区高亮 */}
      <div style={{
        position: 'absolute', top: '35%', height: '30%',
        left: pct(buyLow), right: `${(100 - parseFloat(pct(buyHigh))).toFixed(1)}%`,
        background: 'rgba(102,187,106,0.25)',
        borderRadius: '2px',
      }} />
      {markers.map(({ price, label, color, size }) => (
        <div key={label} style={{
          position: 'absolute', left: pct(price),
          top: '50%', transform: 'translate(-50%, -50%)',
          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px',
        }}>
          <span style={{ fontSize: '10px', color, fontWeight: 600, whiteSpace: 'nowrap' }}>{label}</span>
          <div style={{
            width: size, height: size, borderRadius: '50%',
            background: color, border: '2px solid var(--bg-primary, #fff)',
          }} />
          <span style={{ fontSize: '10px', color: 'var(--text-secondary, #666)', whiteSpace: 'nowrap' }}>
            {fmt(price)}
          </span>
        </div>
      ))}
    </div>
  );
};

const TimeframeContent: React.FC<{ tf: PriceTimeframe; current: number; color: string }> = ({ tf, current, color }) => (
  <div>
    {/* 价格轴 */}
    <PriceBar
      stopLoss={tf.stop_loss}
      buyLow={tf.buy_zone[0]}
      buyHigh={tf.buy_zone[1]}
      current={current}
      t1={tf.targets[0]}
      t2={tf.targets[1]}
      t3={tf.targets[2]}
    />

    {/* 关键数值网格 */}
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '10px', marginTop: '20px',
    }}>
      <div className="metric-card" style={{ padding: '12px' }}>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary, #888)', margin: 0 }}>买入区间</p>
        <p style={{ fontSize: '15px', fontWeight: 700, color: '#66bb6a', margin: '4px 0 0' }}>
          {fmt(tf.buy_zone[0])} ~ {fmt(tf.buy_zone[1])}
        </p>
      </div>
      <div className="metric-card" style={{ padding: '12px' }}>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary, #888)', margin: 0 }}>止损位</p>
        <p style={{ fontSize: '15px', fontWeight: 700, color: '#ef5350', margin: '4px 0 0' }}>
          {fmt(tf.stop_loss)}
        </p>
      </div>
      <div className="metric-card" style={{ padding: '12px' }}>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary, #888)', margin: 0 }}>三档目标价</p>
        <p style={{ fontSize: '13px', fontWeight: 600, color: '#ff9800', margin: '4px 0 0' }}>
          {fmt(tf.targets[0])} / {fmt(tf.targets[1])} / {fmt(tf.targets[2])}
        </p>
      </div>
      <div className="metric-card" style={{ padding: '12px' }}>
        <p style={{ fontSize: '12px', color: 'var(--text-secondary, #888)', margin: 0 }}>盈亏比 / 潜在收益</p>
        <p style={{ margin: '4px 0 0' }}>
          <span style={{
            fontSize: '14px', fontWeight: 700,
            color: rrColor(tf.risk_reward),
          }}>
            {tf.risk_reward}:1
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-secondary, #666)', marginLeft: '8px' }}>
            +{tf.potential_pct}%
          </span>
        </p>
      </div>
    </div>

    {/* 计算依据 */}
    <p style={{
      fontSize: '12px', color: 'var(--text-secondary, #888)',
      margin: '10px 0 0', padding: '6px 10px',
      background: 'var(--bg-secondary, #f5f5f5)', borderRadius: '4px',
    }}>
      计算依据：{tf.basis}
    </p>
  </div>
);

const PriceTargetCard: React.FC<Props> = ({ priceTargets }) => {
  const [activeTab, setActiveTab] = useState<Tab>('short');

  const tfMap: Record<Tab, PriceTimeframe> = {
    short:  priceTargets.short_term,
    medium: priceTargets.medium_term,
    long:   priceTargets.long_term,
  };
  const activeColor = TAB_CONFIG.find(t => t.key === activeTab)!.color;

  return (
    <div className="metric-card" style={{ gridColumn: '1 / -1', padding: '20px' }}>
      <h3 style={{ margin: '0 0 16px', fontSize: '16px' }}>🎯 价格目标</h3>

      {/* Tab 切换 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
        {TAB_CONFIG.map(({ key, label, color }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            style={{
              padding: '6px 14px', borderRadius: '20px', border: 'none',
              cursor: 'pointer', fontSize: '13px', fontWeight: 600,
              background: activeTab === key ? color : 'var(--bg-secondary, #eee)',
              color: activeTab === key ? '#fff' : 'var(--text-primary, #333)',
              transition: 'all 0.2s',
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <TimeframeContent
        tf={tfMap[activeTab]}
        current={priceTargets.current_price}
        color={activeColor}
      />
    </div>
  );
};

export default PriceTargetCard;
