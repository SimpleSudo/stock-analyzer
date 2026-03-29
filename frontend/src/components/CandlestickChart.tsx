import React, { useEffect, useRef, useMemo } from 'react';
import { createChart, ColorType, CrosshairMode } from 'lightweight-charts';
import type { IChartApi } from 'lightweight-charts';
import type { ChartPointWithIndicators } from '../utils/types';

interface CandlestickChartProps {
  data: ChartPointWithIndicators[];
}

/**
 * Lightweight Charts (TradingView 开源版) K 线图
 * - 支持缩放拖拽、十字光标
 * - MA 均线叠加
 * - 成交量子图
 * - A 股配色：涨红跌绿
 */
const CandlestickChart: React.FC<CandlestickChartProps> = ({ data }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  // 转换数据格式
  const candleData = useMemo(() =>
    data
      .filter(d => d.open != null && d.close != null && d.high != null && d.low != null)
      .map(d => ({
        time: d.date as string,
        open: d.open!,
        high: d.high!,
        low: d.low!,
        close: d.close!,
      })),
    [data]
  );

  const volumeData = useMemo(() =>
    data
      .filter(d => d.volume != null && d.close != null && d.open != null)
      .map(d => ({
        time: d.date as string,
        value: d.volume!,
        color: (d.close! >= d.open!) ? 'rgba(239,83,80,0.5)' : 'rgba(38,166,154,0.5)',
      })),
    [data]
  );

  const makeLineSeries = (key: keyof ChartPointWithIndicators) =>
    data
      .filter(d => d[key] != null)
      .map(d => ({ time: d.date as string, value: d[key] as number }));

  useEffect(() => {
    if (!chartContainerRef.current || candleData.length === 0) return;

    // 清理旧图表
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
                   document.querySelector('[data-theme="dark"]') !== null;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 420,
      layout: {
        background: { type: ColorType.Solid, color: isDark ? '#1e1e2e' : '#ffffff' },
        textColor: isDark ? '#cdd6f4' : '#333',
      },
      grid: {
        vertLines: { color: isDark ? '#313244' : '#f0f0f0' },
        horzLines: { color: isDark ? '#313244' : '#f0f0f0' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: isDark ? '#45475a' : '#ddd' },
      timeScale: {
        borderColor: isDark ? '#45475a' : '#ddd',
        timeVisible: false,
      },
    });
    chartRef.current = chart;

    // K 线（A 股配色：涨红跌绿）
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#ef5350',
      downColor: '#26a69a',
      borderUpColor: '#ef5350',
      borderDownColor: '#26a69a',
      wickUpColor: '#ef5350',
      wickDownColor: '#26a69a',
    });
    candleSeries.setData(candleData as any);

    // 成交量（叠加在底部）
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });
    chart.priceScale('volume').applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volumeSeries.setData(volumeData as any);

    // 均线
    const maConfigs: { key: keyof ChartPointWithIndicators; color: string; label: string }[] = [
      { key: 'ma5', color: '#2196f3', label: 'MA5' },
      { key: 'ma10', color: '#ff9800', label: 'MA10' },
      { key: 'ma20', color: '#9c27b0', label: 'MA20' },
      { key: 'ma60', color: '#f44336', label: 'MA60' },
    ];

    for (const { key, color } of maConfigs) {
      const lineData = makeLineSeries(key);
      if (lineData.length > 0) {
        const series = chart.addLineSeries({
          color,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        series.setData(lineData as any);
      }
    }

    // 布林带
    const bbUpper = makeLineSeries('bb_upper');
    const bbLower = makeLineSeries('bb_lower');
    if (bbUpper.length > 0) {
      const upperSeries = chart.addLineSeries({
        color: 'rgba(156,39,176,0.3)',
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      upperSeries.setData(bbUpper as any);
    }
    if (bbLower.length > 0) {
      const lowerSeries = chart.addLineSeries({
        color: 'rgba(156,39,176,0.3)',
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      lowerSeries.setData(bbLower as any);
    }

    chart.timeScale().fitContent();

    // 响应式
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({ width: entry.contentRect.width });
      }
    });
    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [candleData, volumeData]);

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
        📈 K 线图（支持缩放拖拽）
      </h4>
      <div ref={chartContainerRef} style={{ width: '100%' }} />
      <div style={{ fontSize: '11px', color: '#999', marginTop: '4px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <span style={{ color: '#2196f3' }}>■ MA5</span>
        <span style={{ color: '#ff9800' }}>■ MA10</span>
        <span style={{ color: '#9c27b0' }}>■ MA20</span>
        <span style={{ color: '#f44336' }}>■ MA60</span>
        <span style={{ color: 'rgba(156,39,176,0.5)' }}>┄ 布林带</span>
      </div>
    </div>
  );
};

export default CandlestickChart;
