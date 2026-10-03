import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Search, 
  Star,
  ExternalLink
} from 'lucide-react';
import api from '../../api';

export default function ScreenerTable({ 
  tickers = [], 
  onSelectAsset 
}) {
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [sortBy, setSortBy] = useState('gainers');
  const [searchTerm, setSearchTerm] = useState('');
  const [watchlistIds, setWatchlistIds] = useState(new Set());

  // Load user watchlist
  const fetchWatchlist = async () => {
    try {
      const res = await api.get('/watchlist');
      const ids = new Set((res.data.data || []).map(w => w.asset_id));
      setWatchlistIds(ids);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const toggleFavorite = async (e, assetId) => {
    e.stopPropagation();
    try {
      if (watchlistIds.has(assetId)) {
        await api.delete(`/watchlist/${assetId}`);
        setWatchlistIds(prev => {
          const next = new Set(prev);
          next.delete(assetId);
          return next;
        });
      } else {
        await api.post(`/watchlist/${assetId}`);
        setWatchlistIds(prev => new Set(prev).add(assetId));
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Filtering
  const filtered = tickers.filter(item => {
    let matchCategory = true;
    if (categoryFilter === 'watchlist') {
      matchCategory = watchlistIds.has(item.id);
    } else if (categoryFilter === 'crypto') {
      matchCategory = item.asset_type === 'crypto';
    } else if (categoryFilter === 'stock_idx') {
      matchCategory = item.asset_type === 'stock_idx';
    } else if (categoryFilter === 'stock_us') {
      matchCategory = item.asset_type === 'stock_us' || item.asset_type === 'index';
    }

    const matchSearch = 
      item.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.name.toLowerCase().includes(searchTerm.toLowerCase());

    return matchCategory && matchSearch;
  });

  // Sorting
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'gainers') {
      return (b.change_24h_percent || 0) - (a.change_24h_percent || 0);
    } else if (sortBy === 'losers') {
      return (a.change_24h_percent || 0) - (b.change_24h_percent || 0);
    } else if (sortBy === 'volume') {
      return (b.volume_24h || 0) - (a.volume_24h || 0);
    }
    return 0;
  });

  const getSignalBadge = (sig) => {
    switch (sig) {
      case 'strong_buy':
        return { label: 'STRONG BUY', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      case 'buy':
        return { label: 'BUY', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' };
      case 'strong_sell':
        return { label: 'STRONG SELL', color: 'bg-rose-500/10 text-rose-400 border-rose-500/30' };
      case 'sell':
        return { label: 'SELL', color: 'bg-rose-500/10 text-rose-400 border-rose-500/30' };
      default:
        return { label: 'NEUTRAL', color: 'bg-slate-500/10 text-slate-400 border-slate-500/30' };
    }
  };

  return (
    <div className="bg-[#111827] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
      {/* Controls Header */}
      <div className="p-4 sm:p-5 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Category Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 bg-slate-950 p-1.5 rounded-xl border border-slate-800">
          <button
            onClick={() => setCategoryFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              categoryFilter === 'all'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Semua Aset ({tickers.length})
          </button>
          <button
            onClick={() => setCategoryFilter('watchlist')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1 ${
              categoryFilter === 'watchlist'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-amber-400 hover:text-amber-200'
            }`}
          >
            <Star className="w-3.5 h-3.5 fill-amber-400" />
            <span>Favorit ({watchlistIds.size})</span>
          </button>
          <button
            onClick={() => setCategoryFilter('crypto')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              categoryFilter === 'crypto'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Kripto
          </button>
          <button
            onClick={() => setCategoryFilter('stock_idx')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              categoryFilter === 'stock_idx'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Saham IHSG
          </button>
          <button
            onClick={() => setCategoryFilter('stock_us')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              categoryFilter === 'stock_us'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Saham Global (US)
          </button>
        </div>

        {/* Search & Sort by */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter ticker..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono w-40 sm:w-48"
            />
          </div>

          <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs">
            <button
              onClick={() => setSortBy('gainers')}
              className={`px-2.5 py-1 rounded-lg font-mono transition-all ${
                sortBy === 'gainers' ? 'bg-slate-800 text-emerald-400 font-semibold' : 'text-slate-400'
              }`}
            >
              Top Gainers
            </button>
            <button
              onClick={() => setSortBy('losers')}
              className={`px-2.5 py-1 rounded-lg font-mono transition-all ${
                sortBy === 'losers' ? 'bg-slate-800 text-rose-400 font-semibold' : 'text-slate-400'
              }`}
            >
              Top Losers
            </button>
            <button
              onClick={() => setSortBy('volume')}
              className={`px-2.5 py-1 rounded-lg font-mono transition-all ${
                sortBy === 'volume' ? 'bg-slate-800 text-blue-400 font-semibold' : 'text-slate-400'
              }`}
            >
              Volume
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-950/70 border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400 font-mono">
              <th className="py-3 px-3 w-10 text-center">⭐</th>
              <th className="py-3 px-4">Instrumen & Simbol</th>
              <th className="py-3 px-4">Tipe Aset</th>
              <th className="py-3 px-4 text-right">Harga Terakhir</th>
              <th className="py-3 px-4 text-right">Perubahan 24h</th>
              <th className="py-3 px-4 text-right">Volume</th>
              <th className="py-3 px-4 text-center">RSI (14)</th>
              <th className="py-3 px-4 text-center">Sinyal Teknikal</th>
              <th className="py-3 px-4 text-center">Aksi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
            {sorted.map(item => {
              const isPos = (item.change_24h_percent || 0) >= 0;
              const sig = getSignalBadge(item.overall_signal || 'neutral');
              const isIdr = item.base_currency === 'IDR' || item.symbol.endsWith('.JK');
              const isFav = watchlistIds.has(item.id);

              return (
                <tr 
                  key={item.symbol} 
                  onClick={() => onSelectAsset(item.symbol)}
                  className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                >
                  <td className="py-3.5 px-3 text-center" onClick={(e) => toggleFavorite(e, item.id)}>
                    <button className="text-slate-600 hover:text-amber-400 transition-colors p-1">
                      <Star className={`w-4 h-4 ${isFav ? 'fill-amber-400 text-amber-400' : 'text-slate-600'}`} />
                    </button>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="font-bold text-white text-sm group-hover:text-blue-400 transition-colors">
                      {item.symbol}
                    </div>
                    <div className="text-[11px] font-sans text-slate-400">{item.name}</div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider bg-slate-800 text-slate-300">
                      {item.asset_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right font-bold text-slate-100">
                    {isIdr ? `Rp ${item.last_price?.toLocaleString('id-ID')}` : `$${item.last_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}`}
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <span className={`inline-flex items-center gap-1 font-bold ${
                      isPos ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {isPos ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                      {isPos ? '+' : ''}{item.change_24h_percent}%
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right text-slate-400">
                    {item.volume_24h > 1000000 
                      ? `${(item.volume_24h / 1000000).toFixed(2)}M` 
                      : item.volume_24h?.toLocaleString()
                    }
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className={`font-semibold ${
                      (item.rsi_14 || 50) > 70 ? 'text-rose-400' : (item.rsi_14 || 50) < 30 ? 'text-emerald-400' : 'text-slate-300'
                    }`}>
                      {item.rsi_14 ?? '--'}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold border ${sig.color}`}>
                      {sig.label}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectAsset(item.symbol);
                      }}
                      className="p-1.5 rounded-lg bg-slate-800/60 text-slate-400 hover:text-white hover:bg-blue-600 transition-colors"
                      title="Buka Grafik"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
