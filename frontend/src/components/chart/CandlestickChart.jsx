import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

// Helper to calculate EMA array for chart overlays
function calculateEMA(data, period) {
  const k = 2 / (period + 1);
  let emaArray = [];
  let ema = data[0]?.close;

  for (let i = 0; i < data.length; i++) {
    const price = data[i].close;
    if (i === 0) {
      ema = price;
    } else {
      ema = price * k + ema * (1 - k);
    }
    if (i >= period - 1) {
      emaArray.push({ time: data[i].time, value: roundNumber(ema, 2) });
    }
  }
  return emaArray;
}

// Helper to calculate Bollinger Bands array
function calculateBollinger(data, period = 20, multiplier = 2) {
  let upper = [];
  let lower = [];

  for (let i = period - 1; i < data.length; i++) {
    const slice = data.slice(i - period + 1, i + 1).map(d => d.close);
    const mean = slice.reduce((a, b) => a + b, 0) / period;
    const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
    const stdDev = Math.sqrt(variance);

    upper.push({ time: data[i].time, value: roundNumber(mean + (multiplier * stdDev), 2) });
    lower.push({ time: data[i].time, value: roundNumber(mean - (multiplier * stdDev), 2) });
  }

  return { upper, lower };
}

function roundNumber(num, dec) {
  return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
}

export default function CandlestickChart({ bars = [], overlays = {}, height = 480 }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [legend, setLegend] = useState(null);

  useEffect(() => {
    if (!chartContainerRef.current || !bars || bars.length === 0) return;

    // Clear any previous chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const container = chartContainerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height: height,
      layout: {
        background: { type: ColorType.Solid, color: '#090d16' },
        textColor: '#94a3b8',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: 'rgba(31, 41, 55, 0.4)' },
        horzLines: { color: 'rgba(31, 41, 55, 0.4)' },
      },
      crosshair: {
        mode: 1, // Normal crosshair
        vertLine: {
          color: '#3b82f6',
          width: 1,
          style: 3,
          labelBackgroundColor: '#1e293b',
        },
        horzLine: {
          color: '#3b82f6',
          width: 1,
          style: 3,
          labelBackgroundColor: '#1e293b',
        },
      },
      timeScale: {
        borderColor: '#1f2937',
        timeVisible: true,
        secondsVisible: false,
      },
      rightPriceScale: {
        borderColor: '#1f2937',
        scaleMargins: {
          top: 0.1,
          bottom: 0.2, // Leave space for volume histogram
        },
      },
    });

    chartRef.current = chart;

    // 1. Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#f43f5e',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#f43f5e',
    });

    const formattedBars = bars.map(b => ({
      time: b.time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    candleSeries.setData(formattedBars);

    // 2. Volume series
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '', // overlay inside chart
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    const volumeData = bars.map(b => ({
      time: b.time,
      value: b.volume,
      color: b.close >= b.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(244, 63, 94, 0.35)',
    }));
    volumeSeries.setData(volumeData);

    // 3. Technical Indicator Overlays
    if (overlays.ema20 && bars.length >= 20) {
      const ema20Series = chart.addLineSeries({
        color: '#f59e0b',
        lineWidth: 1.5,
        title: 'EMA 20',
      });
      ema20Series.setData(calculateEMA(bars, 20));
    }

    if (overlays.ema50 && bars.length >= 50) {
      const ema50Series = chart.addLineSeries({
        color: '#06b6d4',
        lineWidth: 1.5,
        title: 'EMA 50',
      });
      ema50Series.setData(calculateEMA(bars, 50));
    }

    if (overlays.ema200 && bars.length >= 200) {
      const ema200Series = chart.addLineSeries({
        color: '#a855f7',
        lineWidth: 2,
        title: 'EMA 200',
      });
      ema200Series.setData(calculateEMA(bars, 200));
    }

    if (overlays.bollinger && bars.length >= 20) {
      const { upper, lower } = calculateBollinger(bars, 20, 2);
      const bbUpper = chart.addLineSeries({
        color: 'rgba(99, 102, 241, 0.8)',
        lineWidth: 1,
        lineStyle: 2,
        title: 'BB Upper',
      });
      bbUpper.setData(upper);

      const bbLower = chart.addLineSeries({
        color: 'rgba(99, 102, 241, 0.8)',
        lineWidth: 1,
        lineStyle: 2,
        title: 'BB Lower',
      });
      bbLower.setData(lower);
    }

    // Set default view range to fit all recent bars
    chart.timeScale().fitContent();

    // Crosshair move listener for live legend
    chart.subscribeCrosshairMove((param) => {
      if (!param || !param.time || !param.seriesData) {
        setLegend(null);
        return;
      }
      const data = param.seriesData.get(candleSeries);
      if (data) {
        setLegend({
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
          time: param.time,
        });
      }
    });

    // Auto resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [bars, overlays, height]);

  const latestBar = bars[bars.length - 1];
  const activeBar = legend || latestBar;

  return (
    <div className="relative w-full bg-[#090d16] rounded-b-2xl overflow-hidden border border-t-0 border-slate-800">
      {/* Real-time Bar Info Legend */}
      {activeBar && (
        <div className="absolute top-3 left-4 z-10 flex flex-wrap items-center gap-x-4 gap-y-1 bg-slate-900/80 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-slate-800/80 text-xs font-mono">
          <span className="text-slate-400">O: <strong className="text-slate-200">{activeBar.open}</strong></span>
          <span className="text-slate-400">H: <strong className="text-emerald-400">{activeBar.high}</strong></span>
          <span className="text-slate-400">L: <strong className="text-rose-400">{activeBar.low}</strong></span>
          <span className="text-slate-400">C: <strong className={activeBar.close >= activeBar.open ? "text-emerald-400" : "text-rose-400"}>{activeBar.close}</strong></span>
        </div>
      )}

      {/* Chart Canvas Container */}
      <div ref={chartContainerRef} className="w-full relative" style={{ height: `${height}px` }}>{(!bars || bars.length === 0) && (<div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500 font-mono text-sm gap-3"><div className="w-8 h-8 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin"></div><span>Mengambil data candlestick live dari bursa...</span></div>)}</div>
    </div>
  );
}
