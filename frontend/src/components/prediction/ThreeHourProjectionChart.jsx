import React, { useState, useMemo } from 'react';
import { Clock, TrendingUp, TrendingDown, Layers, Activity, ShieldCheck, Info, Sparkles } from 'lucide-react';

export default function ThreeHourProjectionChart({
  trajectoryData,
  direction = 'NAIK',
  currentPrice = 0,
  targetPrice = 0,
  marketSession = {},
  trajectorySummary = null
}) {
  const [hoveredIndex, setHoveredIndex] = useState(null);

  const isUp = direction === 'NAIK';

  // Process historical & 12 future 15-minute points
  const { historicalPoints, futurePoints, allPrices, minPrice, maxPrice, priceRange } = useMemo(() => {
    const rawHist = trajectoryData?.historical_points || [];
    const rawFuture = trajectoryData?.future_points || [];

    const prices = [];
    rawHist.forEach(p => prices.push(p.close || p.price));
    rawFuture.forEach(p => {
      prices.push(p.projected_price);
      if (p.upper_band) prices.push(p.upper_band);
      if (p.lower_band) prices.push(p.lower_band);
    });

    if (currentPrice) prices.push(currentPrice);
    if (targetPrice) prices.push(targetPrice);

    const baseAnchor = currentPrice || (prices.length ? prices[prices.length - 1] : 100);
    const validPrices = prices.filter(p => Math.abs(p - baseAnchor) / baseAnchor < 0.08);
    const effectivePrices = validPrices.length >= 8 ? validPrices : prices;

    const min = effectivePrices.length ? Math.min(...effectivePrices) : 0;
    const max = effectivePrices.length ? Math.max(...effectivePrices) : 100;
    const padding = (max - min) * 0.10 || min * 0.015 || 1;

    return {
      historicalPoints: rawHist,
      futurePoints: rawFuture,
      allPrices: prices,
      minPrice: min - padding,
      maxPrice: max + padding,
      priceRange: (max + padding) - (min - padding) || 1
    };
  }, [trajectoryData, currentPrice, targetPrice]);

  // Chart Dimensions
  const svgWidth = 920;
  const svgHeight = 340;
  const paddingLeft = 60;
  const paddingRight = 80;
  const paddingTop = 36;
  const paddingBottom = 48;

  const chartWidth = svgWidth - paddingLeft - paddingRight;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  // Split: 32% historical (past 16 candles), 68% future projection (12x 15m intervals)
  const splitRatio = 0.32;
  const splitX = paddingLeft + (chartWidth * splitRatio);

  const getY = (val) => {
    if (!val && val !== 0) return paddingTop + chartHeight / 2;
    const normalized = (val - minPrice) / priceRange;
    return paddingTop + chartHeight - (normalized * chartHeight);
  };

  // Coordinates for historical points
  const histCoords = useMemo(() => {
    if (!historicalPoints.length) return [];
    const stepX = (splitX - paddingLeft) / Math.max(historicalPoints.length - 1, 1);
    return historicalPoints.map((p, idx) => ({
      x: paddingLeft + (idx * stepX),
      y: getY(p.close || p.price),
      data: p
    }));
  }, [historicalPoints, splitX, minPrice, priceRange]);

  // Anchor point at t=0 (current price)
  const currentY = getY(currentPrice);

  // Coordinates for future 12 intervals (each 15m)
  const futureCoords = useMemo(() => {
    if (!futurePoints.length) return [];
    const futureWidth = (svgWidth - paddingRight) - splitX;
    const stepX = futureWidth / futurePoints.length;
    return futurePoints.map((p, idx) => ({
      x: splitX + ((idx + 1) * stepX),
      y: getY(p.projected_price),
      upperY: getY(p.upper_band),
      lowerY: getY(p.lower_band),
      data: p
    }));
  }, [futurePoints, splitX, minPrice, priceRange, svgWidth, paddingRight]);

  // SVG Paths
  const histPathD = useMemo(() => {
    if (!histCoords.length) return '';
    return histCoords.reduce((acc, pt, i) => `${acc} ${i === 0 ? 'M' : 'L'} ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`, '');
  }, [histCoords]);

  const futurePathD = useMemo(() => {
    if (!futureCoords.length) return '';
    let d = `M ${splitX.toFixed(1)} ${currentY.toFixed(1)}`;
    futureCoords.forEach(pt => {
      d += ` L ${pt.x.toFixed(1)} ${pt.y.toFixed(1)}`;
    });
    return d;
  }, [futureCoords, splitX, currentY]);

  // Confidence Corridor Polygon
  const corridorPolygonPoints = useMemo(() => {
    if (!futureCoords.length) return '';
    const upperPoints = [`${splitX.toFixed(1)},${currentY.toFixed(1)}`];
    const lowerPoints = [];

    futureCoords.forEach(pt => {
      upperPoints.push(`${pt.x.toFixed(1)},${pt.upperY.toFixed(1)}`);
      lowerPoints.unshift(`${pt.x.toFixed(1)},${pt.lowerY.toFixed(1)}`);
    });

    return [...upperPoints, ...lowerPoints].join(' ');
  }, [futureCoords, splitX, currentY]);

  // Price Grid Ticks (5 horizontal levels)
  const priceTicks = useMemo(() => {
    const ticks = [];
    for (let i = 0; i <= 4; i++) {
      const p = minPrice + (priceRange * (i / 4));
      ticks.push({
        price: p,
        y: getY(p)
      });
    }
    return ticks;
  }, [minPrice, priceRange]);

  // Active hovered point
  const activeHover = hoveredIndex !== null && futureCoords[hoveredIndex] ? futureCoords[hoveredIndex] : null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Activity className="w-4 h-4" />
            </span>
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider flex items-center space-x-2">
              <span>Lintasan Prediksi 3 Jam Tiap 15 Menit (12 Interval)</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30">
                15M GRANULAR
              </span>
            </h3>
          </div>
          <p className="text-xs text-slate-400">
            Lintasan proyeksi dinamis dari harga t=0 dievaluasi step-by-step setiap 15 menit (+15m s/d +180m) dengan koridor volatilitas kuantitatif.
          </p>
        </div>

        {/* Quick Horizon Badges */}
        <div className="flex items-center space-x-2 shrink-0">
          <div className="flex items-center px-3 py-1 bg-slate-950 rounded-xl border border-slate-800 text-[11px] font-mono text-slate-300">
            <Clock className="w-3.5 h-3.5 text-cyan-400 mr-1.5" />
            <span>12 Interval 15m (180 Menit)</span>
          </div>
        </div>
      </div>

      {/* Market Session Banner */}
      {marketSession?.badge && (
        <div className={`p-3 rounded-xl border text-xs font-mono flex items-center justify-between ${
          marketSession.status === 'MARKET_CLOSED'
            ? 'bg-amber-950/40 border-amber-500/30 text-amber-300'
            : 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
        }`}>
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 shrink-0" />
            <span className="font-bold">{marketSession.badge}:</span>
            <span>{marketSession.horizon_label}</span>
          </div>
          <span className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-slate-950/70 border border-slate-800">
            {marketSession.session_name}
          </span>
        </div>
      )}

      {/* SVG Chart Container */}
      <div className="relative w-full overflow-hidden bg-slate-950/80 rounded-xl border border-slate-800/80 p-2">
        <svg 
          viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
          className="w-full h-auto select-none"
        >
          <defs>
            {/* Bullish Gradient Corridor */}
            <linearGradient id="corridor-grad-bull-15m" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#10B981" stopOpacity="0.28" />
              <stop offset="50%" stopColor="#059669" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#047857" stopOpacity="0.08" />
            </linearGradient>

            {/* Bearish Gradient Corridor */}
            <linearGradient id="corridor-grad-bear-15m" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="#F43F5E" stopOpacity="0.28" />
              <stop offset="50%" stopColor="#E11D48" stopOpacity="0.18" />
              <stop offset="100%" stopColor="#BE123C" stopOpacity="0.08" />
            </linearGradient>
          </defs>

          {/* Horizontal Price Grid Lines & Labels */}
          {priceTicks.map((tick, i) => (
            <g key={i}>
              <line 
                x1={paddingLeft} 
                y1={tick.y} 
                x2={svgWidth - paddingRight} 
                y2={tick.y} 
                stroke="#1e293b" 
                strokeDasharray="2 2" 
                strokeWidth="1" 
              />
              <text 
                x={svgWidth - paddingRight + 8} 
                y={tick.y + 4} 
                fill="#64748b" 
                fontSize="10" 
                fontFamily="monospace"
              >
                {tick.price >= 10 ? tick.price.toLocaleString('en-US', { maximumFractionDigits: 2 }) : tick.price.toFixed(4)}
              </text>
            </g>
          ))}

          {/* Vertical Separator at t=0 (Saat Ini) */}
          <line 
            x1={splitX} 
            y1={paddingTop - 12} 
            x2={splitX} 
            y2={svgHeight - paddingBottom + 12} 
            stroke="#0ea5e9" 
            strokeWidth="1.5" 
            strokeDasharray="3 3" 
            opacity="0.85"
          />

          <text 
            x={splitX} 
            y={paddingTop - 16} 
            fill="#38bdf8" 
            fontSize="10" 
            fontWeight="bold" 
            fontFamily="monospace" 
            textAnchor="middle"
          >
            SAAT INI (t=0)
          </text>

          {/* Historical Zone Label */}
          <text 
            x={(paddingLeft + splitX) / 2} 
            y={svgHeight - 14} 
            fill="#64748b" 
            fontSize="10" 
            fontFamily="monospace" 
            textAnchor="middle"
          >
            Candlestick 15m Historis
          </text>

          {/* Future Zone Label */}
          <text 
            x={(splitX + (svgWidth - paddingRight)) / 2} 
            y={svgHeight - 14} 
            fill={isUp ? '#34d399' : '#fb7185'} 
            fontSize="10" 
            fontWeight="bold" 
            fontFamily="monospace" 
            textAnchor="middle"
          >
            12 Interval Proyeksi (+15m s/d +180m)
          </text>

          {/* Vertical Interval Tick Lines on Future Path */}
          {futureCoords.map((pt, idx) => (
            <g key={`vgrid-${idx}`}>
              <line 
                x1={pt.x} 
                y1={paddingTop} 
                x2={pt.x} 
                y2={svgHeight - paddingBottom} 
                stroke="#1e293b" 
                strokeWidth="0.8" 
                strokeDasharray="2 4"
                opacity="0.6"
              />
              <text 
                x={pt.x} 
                y={svgHeight - paddingBottom + 16} 
                fill="#64748b" 
                fontSize="9" 
                fontFamily="monospace" 
                textAnchor="middle"
              >
                +{pt.data.minutes_ahead}m
              </text>
            </g>
          ))}

          {/* Confidence Volatility Corridor Polygon */}
          {corridorPolygonPoints && (
            <polygon 
              points={corridorPolygonPoints} 
              fill={isUp ? 'url(#corridor-grad-bull-15m)' : 'url(#corridor-grad-bear-15m)'} 
              stroke={isUp ? '#10b981' : '#f43f5e'}
              strokeWidth="0.8"
              strokeDasharray="2 2"
              opacity="0.9"
            />
          )}

          {/* Historical Line */}
          {histPathD && (
            <path 
              d={histPathD} 
              fill="none" 
              stroke="#64748b" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
          )}

          {/* Connect Last Historical to t=0 Anchor */}
          {histCoords.length > 0 && (
            <line 
              x1={histCoords[histCoords.length - 1].x} 
              y1={histCoords[histCoords.length - 1].y} 
              x2={splitX} 
              y2={currentY} 
              stroke="#64748b" 
              strokeWidth="2" 
            />
          )}

          {/* Future Trajectory Line (Dashed) */}
          {futurePathD && (
            <path 
              d={futurePathD} 
              fill="none" 
              stroke={isUp ? '#34d399' : '#fb7185'} 
              strokeWidth="2.5" 
              strokeDasharray="4 3" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
            />
          )}

          {/* Anchor Node: Current Price (t=0) */}
          <circle 
            cx={splitX} 
            cy={currentY} 
            r="5" 
            fill="#0284c7" 
            stroke="#e0f2fe" 
            strokeWidth="2" 
          />

          {/* Interactive Hover Nodes for all 12 Future Points */}
          {futureCoords.map((pt, idx) => {
            const isPeak = trajectorySummary?.peak_target?.step === pt.data.step;
            const isDip = trajectorySummary?.dip_target?.step === pt.data.step;
            const isKeyStep = pt.data.minutes_ahead % 30 === 0 || idx === 11 || isPeak || isDip;

            return (
              <g 
                key={idx}
                className="cursor-pointer"
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
              >
                {/* Invisible large touch hit area */}
                <circle 
                  cx={pt.x} 
                  cy={pt.y} 
                  r="14" 
                  fill="transparent" 
                />
                
                {/* Outer ring for Peak / Dip */}
                {(isPeak || isDip) && (
                  <circle 
                    cx={pt.x} 
                    cy={pt.y} 
                    r="8" 
                    fill="none"
                    stroke={isPeak ? '#34d399' : '#f59e0b'}
                    strokeWidth="1.5"
                    strokeDasharray="2 2"
                    className="animate-pulse"
                  />
                )}

                {/* Visible dot at every 15-minute point */}
                <circle 
                  cx={pt.x} 
                  cy={pt.y} 
                  r={isKeyStep ? '4.5' : '3.0'} 
                  fill={isPeak ? '#10b981' : isDip ? '#f59e0b' : isUp ? '#10b981' : '#f43f5e'} 
                  stroke="#ffffff" 
                  strokeWidth={isKeyStep ? '1.5' : '1.0'} 
                />
              </g>
            );
          })}

          {/* Active Hover Crosshair Line and Tooltip Indicator */}
          {activeHover && (
            <g>
              <line 
                x1={activeHover.x} 
                y1={paddingTop} 
                x2={activeHover.x} 
                y2={svgHeight - paddingBottom} 
                stroke="#38bdf8" 
                strokeWidth="1.2" 
                strokeDasharray="2 2" 
              />
              <circle 
                cx={activeHover.x} 
                cy={activeHover.y} 
                r="7" 
                fill="#38bdf8" 
                stroke="#ffffff" 
                strokeWidth="2.5" 
              />
              <circle 
                cx={activeHover.x} 
                cy={activeHover.upperY} 
                r="3.5" 
                fill="#10b981" 
              />
              <circle 
                cx={activeHover.x} 
                cy={activeHover.lowerY} 
                r="3.5" 
                fill="#f43f5e" 
              />
            </g>
          )}

          {/* Target Price Node at final step (t+3h) */}
          {futureCoords.length > 0 && (
            <g>
              <circle 
                cx={futureCoords[futureCoords.length - 1].x} 
                cy={futureCoords[futureCoords.length - 1].y} 
                r="6" 
                fill={isUp ? '#10b981' : '#f43f5e'} 
                stroke="#ffffff" 
                strokeWidth="2" 
              />
              <text 
                x={futureCoords[futureCoords.length - 1].x} 
                y={futureCoords[futureCoords.length - 1].y - 12} 
                fill={isUp ? '#34d399' : '#fb7185'} 
                fontSize="11" 
                fontWeight="bold" 
                fontFamily="monospace" 
                textAnchor="middle"
              >
                TARGET 3H: {targetPrice?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
              </text>
            </g>
          )}
        </svg>

        {/* Hover Floating Details Card */}
        {activeHover ? (
          <div className="absolute top-4 left-4 p-3.5 bg-slate-900/95 border border-cyan-500/50 rounded-xl shadow-2xl backdrop-blur-md font-mono text-xs text-white space-y-1.5 z-20 max-w-sm">
            <div className="flex items-center justify-between gap-4 text-cyan-300 font-bold border-b border-slate-800 pb-1">
              <span>Interval {activeHover.data.step} ({activeHover.data.interval_label}): {activeHover.data.time_wib}</span>
              <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                activeHover.data.direction === 'NAIK' ? 'bg-emerald-500/20 text-emerald-400' :
                activeHover.data.direction === 'TURUN' ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-800 text-slate-300'
              }`}>
                {activeHover.data.direction}
              </span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-slate-400">Target Harga:</span>
              <span className="font-bold text-white text-sm">
                {activeHover.data.projected_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                <span className={`ml-2 text-xs ${activeHover.data.change_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {activeHover.data.change_percent >= 0 ? '+' : ''}{activeHover.data.change_percent}%
                </span>
              </span>
            </div>
            <div className="flex items-center justify-between gap-4 text-[11px]">
              <span className="text-slate-400">Probabilitas:</span>
              <span className="text-cyan-300 font-bold">{activeHover.data.probability_percent}%</span>
            </div>
            <div className="flex items-center justify-between gap-4 text-[11px]">
              <span className="text-slate-400">Rentang Volatilitas:</span>
              <span className="text-slate-200">
                {activeHover.data.lower_band?.toLocaleString('en-US', { maximumFractionDigits: 2 })} - {activeHover.data.upper_band?.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </span>
            </div>
            {activeHover.data.take_profit_price && (
              <div className="flex items-center justify-between gap-4 text-[10px] font-mono pt-1 border-t border-slate-800">
                <span className="text-emerald-400 font-bold">TP: {activeHover.data.take_profit_price?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
                <span className="text-rose-400 font-bold">SL: {activeHover.data.stop_loss_price?.toLocaleString('en-US', { maximumFractionDigits: 2 })}</span>
              </div>
            )}
            <div className="pt-1 text-[11px] font-sans text-slate-300 border-t border-slate-800/80 leading-snug">
              <span className="text-cyan-400 font-mono text-[10px] uppercase font-bold block mb-0.5">Katalis Mikro:</span>
              {activeHover.data.catalyst}
            </div>
          </div>
        ) : (
          <div className="absolute top-4 left-4 px-3 py-1.5 bg-slate-900/85 border border-slate-800 rounded-lg font-mono text-[11px] text-slate-400 flex items-center space-x-2 pointer-events-none">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Arahkan kursor pada 12 titik milestone untuk melihat rincian per 15 menit</span>
          </div>
        )}
      </div>

      {/* Legend and Guidance Footer */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs font-mono text-slate-400">
        <div className="flex items-center space-x-2">
          <span className="w-4 h-0.5 bg-slate-500 rounded" />
          <span>Garis Abu-abu: Tren Riil 15M Historis</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`w-4 h-0.5 border-t-2 border-dashed ${isUp ? 'border-emerald-400' : 'border-rose-400'}`} />
          <span>Garis Putus: Lintasan Proyeksi 12 Interval 15m</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`w-3.5 h-3.5 rounded border ${
            isUp ? 'bg-emerald-500/20 border-emerald-500/40' : 'bg-rose-500/20 border-rose-500/40'
          }`} />
          <span>Corong Volatilitas ATR 15m (90% Conf)</span>
        </div>
      </div>
    </div>
  );
}
