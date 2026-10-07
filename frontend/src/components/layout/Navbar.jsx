import React, { useState } from 'react';
import { 
  FinblixLogo, 
  CryptoOrbitIcon, 
  GlobalMarketIcon,
  ThreeHourRadarIcon 
} from '../icons/CustomIcons';
import { 
  Compass, 
  Search, 
  TrendingUp, 
  TrendingDown, 
  ListFilter, 
  Newspaper,
  Bell
} from 'lucide-react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  selectedSymbol, 
  setSelectedSymbol, 
  tickers = [],
  onOpenAlerts,
  alertsCount = 0
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  // Categorize searched tickers
  const searchResults = searchQuery.trim() 
    ? tickers.filter(t => 
        t.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.name.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const cryptoResults = searchResults.slice(0, 8);
  const totalResultsCount = cryptoResults.length;

  const handleSelectSymbol = (sym) => {
    setSelectedSymbol(sym);
    setIsSearchOpen(false);
    setSearchQuery('');
    setActiveTab('prediction');
  };

  return (
    <header className="sticky top-0 z-40 bg-[#0b0f19]/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        
        {/* Brand */}
        <div 
          className="flex items-center space-x-3 cursor-pointer shrink-0 group" 
          onClick={() => setActiveTab('prediction')}
        >
          <div className="relative shrink-0">
            <FinblixLogo className="w-9 h-9 transition-transform group-hover:scale-105 duration-200" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-lg font-black tracking-tight text-white font-mono">
                FINBLIX
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono">
                PREDICTION AI
              </span>
            </div>
            <div className="text-[10px] font-mono text-slate-400 tracking-wider uppercase -mt-0.5">
              Daily Directional Forecast
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative flex-1 max-w-md hidden md:block">
          <div className="relative flex items-center">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Cari aset kripto (contoh: BTC/USDT, ETH/USDT, SOL/USDT)..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setIsSearchOpen(true);
              }}
              onFocus={() => setIsSearchOpen(true)}
              className="w-full bg-slate-900/90 border border-slate-800 focus:border-blue-500/80 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500/50 transition-all font-mono"
            />
          </div>

          {/* Search Dropdown - Crypto 24/7 */}
          {isSearchOpen && searchQuery.trim() && (
            <div 
              className="absolute left-0 right-0 mt-2 bg-[#0c1220] border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden z-50 divide-y divide-slate-800/80 max-h-[460px] overflow-y-auto"
              onMouseLeave={() => setIsSearchOpen(false)}
            >
              {totalResultsCount > 0 ? (
                <div className="space-y-2 p-1.5">
                  <div className="space-y-1">
                    <div className="px-3 py-1 text-[10px] font-mono font-bold text-purple-400 uppercase tracking-wider bg-purple-950/30 rounded flex items-center justify-between">
                      <span className="flex items-center space-x-1.5">
                        <CryptoOrbitIcon className="w-3.5 h-3.5 text-purple-400" />
                        <span>Pasar Kripto (Crypto 24/7)</span>
                      </span>
                      <span className="text-[9px] text-purple-500/80">Microstructure Engine</span>
                    </div>
                    {cryptoResults.map((t) => (
                      <div
                        key={t.symbol}
                        onClick={() => handleSelectSymbol(t.symbol)}
                        className="p-2.5 hover:bg-slate-800/70 rounded-xl cursor-pointer flex items-center justify-between text-xs font-mono transition-colors"
                      >
                        <div>
                          <div className="font-bold text-white flex items-center space-x-1.5">
                            <span className="text-purple-300">{t.symbol}</span>
                            <span className="text-[10px] text-slate-400 font-normal">24/7</span>
                          </div>
                          <div className="text-[11px] text-slate-400 font-sans truncate max-w-[220px]">{t.name}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-bold text-slate-200">
                            ${t.last_price?.toLocaleString('en-US')}
                          </div>
                          <div className={`text-[10px] flex items-center justify-end space-x-0.5 font-bold ${
                            (t.change_24h_percent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                          }`}>
                            {(t.change_24h_percent || 0) >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            <span>{(t.change_24h_percent || 0) >= 0 ? '+' : ''}{t.change_24h_percent}%</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-5 text-xs text-slate-500 text-center font-sans">
                  Tidak ada aset ditemukan untuk pencarian "{searchQuery}"
                </div>
              )}
            </div>
          )}
        </div>

        {/* Tab Buttons and Alert Bell */}
        <div className="flex items-center space-x-2">
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('prediction')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold font-mono transition-all ${
                activeTab === 'prediction'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Compass className="w-4 h-4" />
              <span>Dashboard Harian</span>
            </button>

            <button
              onClick={() => setActiveTab('three-hours')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold font-mono transition-all ${
                activeTab === 'three-hours'
                  ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <ThreeHourRadarIcon className="w-4 h-4 text-cyan-300" />
              <span>Prediksi 3 Jam</span>
            </button>

            <button
              onClick={() => setActiveTab('screener')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold font-mono transition-all ${
                activeTab === 'screener'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <ListFilter className="w-4 h-4" />
              <span>Screener Prediksi</span>
            </button>

            <button
              onClick={() => setActiveTab('news')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold font-mono transition-all ${
                activeTab === 'news'
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Newspaper className="w-4 h-4" />
              <span>Sentimen Berita</span>
            </button>
          </nav>

          {/* Anomaly Alerts Notification Bell */}
          <button
            onClick={onOpenAlerts}
            className="relative p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition-colors ml-1"
            title="Peringatan Anomali dan Spike Volume"
          >
            <Bell className="w-4 h-4" />
            {alertsCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-rose-500 ring-2 ring-[#0b0f19] animate-pulse" />
            )}
          </button>
        </div>

      </div>
    </header>
  );
}
