import React, { useState } from 'react';
import { LayoutGrid, TrendingUp, TrendingDown, ExternalLink } from 'lucide-react';

export default function MarketHeatmapView({ tickers = [], onSelectAsset }) {
  const [filterType, setFilterType] = useState('all');

  const filtered = tickers.filter(t => {
    if (filterType === 'all') return true;
    if (filterType === 'crypto') return t.asset_type === 'crypto';
    if (filterType === 'stock_idx') return t.asset_type === 'stock_idx';
    if (filterType === 'stock_us') return t.asset_type === 'stock_us' || t.asset_type === 'index';
    return true;
  });

  // Determine heatmap tile color based on 24h %
  const getTileColor = (pct) => {
    if (pct >= 5.0) return 'bg-emerald-600 border-emerald-400 text-white shadow-emerald-500/20';
    if (pct >= 1.5) return 'bg-emerald-700/80 border-emerald-500 text-emerald-100';
    if (pct > 0.0) return 'bg-emerald-900/60 border-emerald-700 text-emerald-200';
    if (pct <= -5.0) return 'bg-rose-600 border-rose-400 text-white shadow-rose-500/20';
    if (pct <= -1.5) return 'bg-rose-700/80 border-rose-500 text-rose-100';
    if (pct < 0.0) return 'bg-rose-900/60 border-rose-700 text-rose-200';
    return 'bg-slate-800 border-slate-700 text-slate-300';
  };

  // Determine relative size (large for BTC, NVDA, BBCA, medium for others)
  const getTileSpan = (symbol) => {
    if (['BTC/USDT', 'NVDA', 'BBCA.JK', 'ETH/USDT', 'AAPL'].includes(symbol)) {
      return 'col-span-2 row-span-2 min-h-[140px]';
    }
    return 'col-span-1 row-span-1 min-h-[100px]';
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-white font-mono flex items-center space-x-2">
            <LayoutGrid className="w-5 h-5 text-blue-400" />
            <span>MARKET HEATMAP GRID</span>
          </h2>
          <p className="text-xs text-slate-400">
            Peta visual performa pasar ala Finviz / Coin360. Klik kotak mana saja untuk membuka grafik aset.
          </p>
        </div>

        <div className="flex items-center space-x-1.5 bg-slate-950 p-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setFilterType('all')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              filterType === 'all' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Semua ({tickers.length})
          </button>
          <button
            onClick={() => setFilterType('crypto')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              filterType === 'crypto' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Kripto
          </button>
          <button
            onClick={() => setFilterType('stock_idx')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              filterType === 'stock_idx' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Saham IHSG
          </button>
          <button
            onClick={() => setFilterType('stock_us')}
            className={`px-3 py-1.5 rounded-lg transition-all ${
              filterType === 'stock_us' ? 'bg-blue-600 text-white font-bold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Saham US
          </button>
        </div>
      </div>

      {/* Heatmap Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {filtered.map(t => {
          const chg = t.change_24h_percent || 0;
          const isPos = chg >= 0;
          const colorClass = getTileColor(chg);
          const spanClass = getTileSpan(t.symbol);
          const isIdr = t.base_currency === 'IDR' || t.symbol.endsWith('.JK');

          return (
            <div
              key={t.symbol}
              onClick={() => onSelectAsset(t.symbol)}
              className={`p-4 rounded-2xl border transition-all duration-200 hover:scale-[1.02] cursor-pointer flex flex-col justify-between shadow-lg relative group ${colorClass} ${spanClass}`}
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="text-base sm:text-lg font-black font-mono tracking-tight leading-tight">
                    {t.symbol}
                  </div>
                  <div className="text-[11px] opacity-80 truncate max-w-[120px] font-sans">
                    {t.name}
                  </div>
                </div>
                <ExternalLink className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>

              <div className="mt-2 flex items-baseline justify-between font-mono">
                <div className="text-xs sm:text-sm font-bold opacity-90">
                  {isIdr ? `Rp ${t.last_price?.toLocaleString('id-ID')}` : `$${t.last_price?.toLocaleString('en-US')}`}
                </div>
                <div className="text-sm sm:text-base font-black flex items-center space-x-0.5">
                  {isPos ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  <span>{isPos ? '+' : ''}{chg}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
