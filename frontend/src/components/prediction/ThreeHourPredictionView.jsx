import React, { useState, useEffect } from 'react';
import { 
  getThreeHourPrediction, 
  trainThreeHourModel, 
  triggerBulkScrapeNews 
} from '../../api';
import { 
  ThreeHourRadarIcon, 
  FinblixLogo, 
  IdxEmblemIcon, 
  CryptoOrbitIcon, 
  GlobalMarketIcon 
} from '../icons/CustomIcons';
import ThreeHourProjectionChart from './ThreeHourProjectionChart';
import { 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  Clock, 
  Zap, 
  Activity, 
  CheckCircle2, 
  XCircle, 
  BarChart2, 
  Layers, 
  Newspaper, 
  Compass, 
  AlertCircle,
  ShieldCheck,
  ChevronRight,
  Database
} from 'lucide-react';

const PRESET_ASSETS = [
  { symbol: 'BTC/USDT', name: 'Bitcoin', type: 'crypto' },
  { symbol: 'ETH/USDT', name: 'Ethereum', type: 'crypto' },
  { symbol: 'SOL/USDT', name: 'Solana', type: 'crypto' },
  { symbol: 'BBCA.JK', name: 'Bank Central Asia', type: 'idx' },
  { symbol: 'BBRI.JK', name: 'Bank Rakyat Indonesia', type: 'idx' },
  { symbol: 'BMRI.JK', name: 'Bank Mandiri', type: 'idx' },
  { symbol: 'TLKM.JK', name: 'Telkom Indonesia', type: 'idx' },
  { symbol: 'ASII.JK', name: 'Astra International', type: 'idx' },
  { symbol: 'ICBP.JK', name: 'Indofood CBP', type: 'idx' },
  { symbol: 'NVDA', name: 'Nvidia Corp', type: 'us' },
  { symbol: 'AAPL', name: 'Apple Inc', type: 'us' }
];

export default function ThreeHourPredictionView({ tickers = [], defaultSymbol = 'BTC/USDT' }) {
  const [selectedSymbol, setSelectedSymbol] = useState(defaultSymbol);
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [predictionData, setPredictionData] = useState(null);
  const [error, setError] = useState(null);

  // Action states
  const [training, setTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState(null);
  const [scraping, setScraping] = useState(false);
  const [scrapeResult, setScrapeResult] = useState(null);

  // Fetch 3-Hour prediction
  const fetchPrediction = async (sym) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getThreeHourPrediction(sym);
      if (res.data?.status === 'success') {
        setPredictionData(res.data.data);
      } else {
        setError(res.data?.message || 'Gagal memuat proyeksi 3 jam');
      }
    } catch (err) {
      console.error('Fetch 3H prediction error:', err);
      setError('Terjadi kendala saat memuat data prediksi 3 jam.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction(selectedSymbol);
  }, [selectedSymbol]);

  // Handle re-training 7D model
  const handleTrainModel = async () => {
    setTraining(true);
    setTrainMessage(null);
    try {
      const res = await trainThreeHourModel(selectedSymbol);
      if (res.data?.status === 'success') {
        const d = res.data.data;
        const acc = d?.test_accuracy_pct || res.data.metrics?.backtest_accuracy_percent || 0;
        setTrainMessage(`Model 7 hari berhasil dilatih ulang (${d?.samples_trained || 114} bar teruji)! Akurasi validasi: ${acc}% (durasi: ${d?.duration_seconds || 1.2}s)`);
        await fetchPrediction(selectedSymbol);
      } else {
        setTrainMessage('Pelatihan model selesai.');
      }
    } catch (err) {
      console.error('Training error:', err);
      setTrainMessage('Pelatihan model gagal atau waktu habis.');
    } finally {
      setTraining(false);
    }
  };

  // Handle trigger bulk daily news scraping
  const handleBulkScrape = async () => {
    setScraping(true);
    setScrapeResult(null);
    try {
      const res = await triggerBulkScrapeNews(25);
      if (res.data?.status === 'success') {
        setScrapeResult(res.data.data);
        await fetchPrediction(selectedSymbol);
      }
    } catch (err) {
      console.error('Scrape error:', err);
    } finally {
      setScraping(false);
    }
  };

  const filteredAssets = PRESET_ASSETS.filter(a => {
    if (activeCategory === 'crypto') return a.type === 'crypto';
    if (activeCategory === 'idx') return a.type === 'idx';
    if (activeCategory === 'us') return a.type === 'us';
    return true;
  });

  const pred = predictionData?.prediction_3h || predictionData?.prediction;
  const targetPrice = predictionData?.target_price;
  const microSignals = predictionData?.micro_signals;
  const backtest = predictionData?.backtest_7d_accuracy;
  const newsSentiment = predictionData?.daily_news_sentiment || predictionData?.scraped_news_summary;
  const marketSession = predictionData?.market_session;
  const trajectoryData = predictionData?.trajectory_5m;

  const isUp = pred?.direction === 'NAIK';
  const isDown = pred?.direction === 'TURUN';

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-[#0d1527] to-slate-900 border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden shadow-xl">
        <div className="absolute -top-12 -right-12 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="p-2 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-400">
                <ThreeHourRadarIcon className="w-6 h-6 text-cyan-400" />
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase bg-blue-500/10 text-blue-400 border border-blue-500/20">
                INTRADAY HORIZON: T+3 JAM
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                TRAINING WINDOW: 7 HARI TERAKHIR
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white font-mono">
              PREDIKSI 3 JAM KE DEPAN
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
              Model Intraday Ensemble (Random Forest 150 + HistGradientBoosting 100) dilatih menggunakan data per jam selama 7 hari ke belakang (168 bar), dipadukan dengan scraping massal berita finansial harian untuk proyeksi arah pergerakan harga 3 jam ke depan.
            </p>
          </div>

          {/* Action Buttons: Scraping & Training */}
          <div className="flex flex-wrap sm:flex-nowrap items-center gap-3 shrink-0">
            <button
              onClick={handleBulkScrape}
              disabled={scraping}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-mono font-bold border transition-all ${
                scraping 
                  ? 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed' 
                  : 'bg-cyan-950/60 hover:bg-cyan-900/80 text-cyan-300 border-cyan-500/40 hover:border-cyan-400 shadow-lg shadow-cyan-950/50'
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${scraping ? 'animate-spin text-cyan-400' : ''}`} />
              <span>{scraping ? 'Scraping Massal...' : 'Scrape Berita Harian'}</span>
            </button>

            <button
              onClick={handleTrainModel}
              disabled={training}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-mono font-bold border transition-all ${
                training 
                  ? 'bg-slate-800 text-slate-500 border-slate-700 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-500 text-white border-blue-400/40 shadow-lg shadow-blue-600/30'
              }`}
            >
              <Zap className={`w-4 h-4 ${training ? 'animate-bounce text-amber-300' : ''}`} />
              <span>{training ? 'Melatih 7 Hari...' : 'Latih Ulang Model 7D'}</span>
            </button>
          </div>
        </div>

        {/* Live Notification Bar after training/scraping */}
        {trainMessage && (
          <div className="mt-4 p-3 rounded-xl bg-blue-950/50 border border-blue-500/30 text-xs font-mono text-blue-300 flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-blue-400" />
              <span>{trainMessage}</span>
            </span>
            <button onClick={() => setTrainMessage(null)} className="text-slate-400 hover:text-white text-xs">Tutup</button>
          </div>
        )}

        {scrapeResult && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-950/50 border border-emerald-500/30 text-xs font-mono text-emerald-300 flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>
                Scraping massal selesai: +{scrapeResult.new_articles_scraped} artikel baru ({scrapeResult.total_articles_in_db} total artikel di database). Sentimen agregat: {scrapeResult.sentiment_summary?.label} ({scrapeResult.sentiment_summary?.average_score}).
              </span>
            </span>
            <button onClick={() => setScrapeResult(null)} className="text-slate-400 hover:text-white text-xs">Tutup</button>
          </div>
        )}
      </div>

      {/* Asset Selection Bar */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveCategory('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                activeCategory === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              Semua Aset
            </button>
            <button
              onClick={() => setActiveCategory('crypto')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                activeCategory === 'crypto'
                  ? 'bg-purple-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <CryptoOrbitIcon className="w-3.5 h-3.5" />
              <span>Kripto (24/7)</span>
            </button>
            <button
              onClick={() => setActiveCategory('idx')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                activeCategory === 'idx'
                  ? 'bg-emerald-600 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <IdxEmblemIcon className="w-3.5 h-3.5" />
              <span>Saham IDX (BEI)</span>
            </button>
            <button
              onClick={() => setActiveCategory('us')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                activeCategory === 'us'
                  ? 'bg-blue-500 text-white'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
            >
              <GlobalMarketIcon className="w-3.5 h-3.5" />
              <span>Wall Street (US)</span>
            </button>
          </div>

          <div className="text-[11px] font-mono text-slate-400 flex items-center space-x-2">
            <span>Aset Terpilih:</span>
            <span className="font-bold text-white px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
              {selectedSymbol}
            </span>
          </div>
        </div>

        {/* Ticker Badges Grid */}
        <div className="flex flex-wrap gap-2 pt-1">
          {filteredAssets.map(a => {
            const isSelected = a.symbol === selectedSymbol;
            return (
              <button
                key={a.symbol}
                onClick={() => setSelectedSymbol(a.symbol)}
                className={`px-3 py-2 rounded-xl text-xs font-mono font-bold transition-all flex items-center space-x-2 border ${
                  isSelected
                    ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400 shadow-md shadow-cyan-950/50'
                    : 'bg-slate-950/60 hover:bg-slate-800/80 text-slate-300 border-slate-800 hover:border-slate-700'
                }`}
              >
                {a.type === 'crypto' && <CryptoOrbitIcon className="w-3.5 h-3.5 text-purple-400" />}
                {a.type === 'idx' && <IdxEmblemIcon className="w-3.5 h-3.5 text-emerald-400" />}
                {a.type === 'us' && <GlobalMarketIcon className="w-3.5 h-3.5 text-blue-400" />}
                <span>{a.symbol}</span>
                <span className="text-[10px] text-slate-500 font-sans font-normal truncate max-w-[90px]">{a.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-16 flex flex-col items-center justify-center space-y-4 text-center">
          <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
          <div className="space-y-1">
            <h3 className="text-sm font-bold font-mono text-white">Memproses Data 168 Bar (7 Hari) & Prediksi 3 Jam...</h3>
            <p className="text-xs text-slate-400">Menghitung micro-momentum, ekstrasi fitur intraday, dan komparasi sentimen.</p>
          </div>
        </div>
      ) : error ? (
        <div className="bg-rose-950/30 border border-rose-800/60 rounded-2xl p-8 flex items-center space-x-4 text-rose-300">
          <AlertCircle className="w-6 h-6 shrink-0 text-rose-400" />
          <div className="space-y-1">
            <div className="font-bold font-mono text-sm">Gagal Mengambil Proyeksi 3 Jam</div>
            <div className="text-xs text-rose-300/80">{error}</div>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Primary Bento Row: Hero Direction & Target Price Range */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            
            {/* Card 1: Hero Directional Outlook (Col 5) */}
            <div className="lg:col-span-5 bg-gradient-to-b from-slate-900 to-[#0b101d] border border-slate-800 rounded-2xl p-6 relative overflow-hidden flex flex-col justify-between shadow-xl">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
                  <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider">
                    Keputusan Model 3 Jam
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-lg border border-slate-700 flex items-center space-x-1.5">
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Target: {marketSession?.target_time_wib || predictionData?.target_time_utc || 'T+3 Jam'}</span>
                </div>
              </div>

              {/* Big Direction Badge */}
              <div className="py-6 flex flex-col items-center justify-center text-center space-y-3">
                <div className={`w-20 h-20 rounded-2xl flex items-center justify-center border ${
                  isUp 
                    ? 'bg-emerald-950/60 border-emerald-500/40 text-emerald-400 shadow-xl shadow-emerald-950/60'
                    : isDown 
                    ? 'bg-rose-950/60 border-rose-500/40 text-rose-400 shadow-xl shadow-rose-950/60'
                    : 'bg-amber-950/60 border-amber-500/40 text-amber-400 shadow-xl shadow-amber-950/60'
                }`}>
                  {isUp && <TrendingUp className="w-10 h-10 stroke-[2.5]" />}
                  {isDown && <TrendingDown className="w-10 h-10 stroke-[2.5]" />}
                  {!isUp && !isDown && <Activity className="w-10 h-10" />}
                </div>

                <div className="space-y-1">
                  <div className={`text-3xl font-black font-mono tracking-tight ${
                    isUp ? 'text-emerald-400' : isDown ? 'text-rose-400' : 'text-amber-400'
                  }`}>
                    PROYEKSI: {pred?.direction}
                  </div>
                  <div className="text-xs font-mono text-slate-400">
                    Probabilitas Arah: <span className="font-bold text-white">{pred?.probability_percent}%</span>
                  </div>
                </div>

                <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-mono font-bold bg-slate-800/80 border border-slate-700 text-slate-300">
                  <span>Tingkat Keyakinan:</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] ${
                    pred?.conviction_tier === 'HIGH CONVICTION' ? 'bg-emerald-500/20 text-emerald-300' :
                    pred?.conviction_tier === 'MODERATE' ? 'bg-cyan-500/20 text-cyan-300' :
                    'bg-slate-700 text-slate-300'
                  }`}>
                    {pred?.conviction_tier}
                  </span>
                </div>
              </div>

              {/* Bottom Quick Return Stats */}
              <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-800 text-xs font-mono">
                <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 uppercase">Ekspektasi Return 3 Jam</div>
                  <div className={`text-base font-bold mt-0.5 ${
                    (targetPrice?.expected_return_percent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {(targetPrice?.expected_return_percent || 0) >= 0 ? '+' : ''}{targetPrice?.expected_return_percent}%
                  </div>
                </div>
                <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
                  <div className="text-[10px] text-slate-400 uppercase">Rezim Intraday</div>
                  <div className="text-xs font-bold text-cyan-300 mt-1 truncate">
                    {predictionData?.intraday_regime}
                  </div>
                </div>
              </div>
            </div>

            {/* Card 2: Target Price Range & Volatility Corridor (Col 7) */}
            <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between shadow-xl">
              <div>
                <div className="flex items-center justify-between pb-4 border-b border-slate-800">
                  <div className="flex items-center space-x-2">
                    <BarChart2 className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                      Koridor Harga Proyeksi & Batas Volatilitas
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                    ATR & Bollinger Volatility Bands
                  </span>
                </div>

                {/* Big Metric Display */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-5">
                  <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                    <div className="text-xs font-mono text-slate-400 uppercase">Harga Terkini (t=0)</div>
                    <div className="text-2xl font-black font-mono text-white">
                      {targetPrice?.current_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-slate-500 font-mono">Bar penutupan jam terakhir</div>
                  </div>

                  <div className="p-4 bg-cyan-950/30 border border-cyan-500/30 rounded-xl space-y-1">
                    <div className="text-xs font-mono text-cyan-400 uppercase">Estimasi Target 3 Jam (t+3)</div>
                    <div className={`text-2xl font-black font-mono ${
                      isUp ? 'text-emerald-400' : isDown ? 'text-rose-400' : 'text-cyan-300'
                    }`}>
                      {targetPrice?.projected_target_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-[10px] text-cyan-300/70 font-mono">
                      Pergeseran {(targetPrice?.expected_return_percent || 0) >= 0 ? '+' : ''}{targetPrice?.expected_return_percent}%
                    </div>
                  </div>
                </div>

                {/* Corridor Range Bar */}
                <div className="space-y-2 pt-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-rose-400 font-bold">
                      Batas Bawah: {targetPrice?.volatility_lower_band?.toLocaleString('en-US')}
                    </span>
                    <span className="text-slate-400 text-[11px]">Rentang Toleransi Volatilitas</span>
                    <span className="text-emerald-400 font-bold">
                      Batas Atas: {targetPrice?.volatility_upper_band?.toLocaleString('en-US')}
                    </span>
                  </div>

                  {/* Visual Progress Spread */}
                  <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 flex">
                    <div className="w-1/4 bg-rose-500/30 border-r border-rose-500/50" />
                    <div className="w-2/4 bg-blue-500/20 flex items-center justify-center">
                      <div className="w-1.5 h-full bg-cyan-400 shadow-lg shadow-cyan-400/80 animate-pulse" />
                    </div>
                    <div className="w-1/4 bg-emerald-500/30 border-l border-emerald-500/50" />
                  </div>
                </div>
              </div>

              {/* Explanatory summary */}
              <div className="mt-5 p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 text-[11px] font-mono text-slate-400 flex items-center space-x-2">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>
                  Batas atas dan batas bawah dikalkulasi secara dinamis menggunakan ATR 1-jam dan standar deviasi Bollinger Bands (2.0 SD) dari 168 bar training.
                </span>
              </div>
            </div>
          </div>

          {/* CENTERPIECE: INTERACTIVE 3-HOUR PROJECTION TRAJECTORY CHART (5M VOLATILITY FUNNEL) */}
          <ThreeHourProjectionChart
            trajectoryData={trajectoryData}
            direction={pred?.direction}
            currentPrice={targetPrice?.current_price}
            targetPrice={targetPrice?.projected_target_price}
            marketSession={marketSession}
          />

          {/* Secondary Bento Row: Micro-Momentum Indicators & Daily Bulk News Sentiment */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

            {/* Micro-Momentum Indicators Card (Col 6) */}
            <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                    Indikator Micro-Momentum Intraday (1H)
                  </span>
                </div>
                <span className="text-[10px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  16 Fitur Intraday
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 font-mono">
                {/* RSI 1H */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">RSI (1-Jam)</div>
                  <div className="text-base font-bold text-white">{microSignals?.rsi_1h}</div>
                  <div className={`text-[10px] ${
                    (microSignals?.rsi_1h || 50) > 70 ? 'text-rose-400' :
                    (microSignals?.rsi_1h || 50) < 30 ? 'text-emerald-400' : 'text-slate-400'
                  }`}>
                    {(microSignals?.rsi_1h || 50) > 70 ? 'Overbought' :
                     (microSignals?.rsi_1h || 50) < 30 ? 'Oversold' : 'Netral'}
                  </div>
                </div>

                {/* EMA 9 Alignment */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">Harga vs EMA 9</div>
                  <div className="text-base font-bold text-white">{microSignals?.price_vs_ema9}</div>
                  <div className={`text-[10px] font-bold ${
                    microSignals?.price_vs_ema9 === 'ABOVE' ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {microSignals?.price_vs_ema9 === 'ABOVE' ? 'Di Atas EMA' : 'Di Bawah EMA'}
                  </div>
                </div>

                {/* EMA Slope */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">Slope Tren EMA</div>
                  <div className="text-base font-bold text-white">{microSignals?.ema_slope}</div>
                  <div className={`text-[10px] ${
                    microSignals?.ema_slope === 'UP' ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {microSignals?.ema_slope === 'UP' ? 'Tren Naik' : 'Tren Melemah'}
                  </div>
                </div>

                {/* MACD Histogram */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">MACD Hist (1H)</div>
                  <div className="text-base font-bold text-white">{microSignals?.macd_histogram}</div>
                  <div className={`text-[10px] ${
                    (microSignals?.macd_histogram || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {(microSignals?.macd_histogram || 0) >= 0 ? 'Momentum Positif' : 'Momentum Negatif'}
                  </div>
                </div>

                {/* CMF 12H */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">Chaikin Money Flow</div>
                  <div className="text-base font-bold text-white">{microSignals?.chaikin_money_flow_12h}</div>
                  <div className={`text-[10px] ${
                    (microSignals?.chaikin_money_flow_12h || 0) > 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {(microSignals?.chaikin_money_flow_12h || 0) > 0 ? 'Inflow Akumulasi' : 'Outflow Distribusi'}
                  </div>
                </div>

                {/* Volume Surge */}
                <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl space-y-1">
                  <div className="text-[10px] text-slate-400 uppercase">Volume Surge</div>
                  <div className="text-base font-bold text-white">{microSignals?.volume_surge_ratio}x</div>
                  <div className={`text-[10px] ${
                    (microSignals?.volume_surge_ratio || 1) > 1.3 ? 'text-amber-400 font-bold' : 'text-slate-400'
                  }`}>
                    {(microSignals?.volume_surge_ratio || 1) > 1.3 ? 'Spike Volume' : 'Volume Normal'}
                  </div>
                </div>
              </div>

              {/* Micro Return Sequence (1h, 2h, 3h, 6h) */}
              <div className="pt-2 border-t border-slate-800">
                <div className="text-[11px] font-mono text-slate-400 mb-2">Rentang Retur Historis Terakhir (Jam ke Belakang):</div>
                <div className="grid grid-cols-4 gap-2 font-mono text-center">
                  <div className="p-2 bg-slate-950/50 rounded-lg border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase">Retur 1-Jam</div>
                    <div className={`text-xs font-bold ${
                      (microSignals?.return_1h_percent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {(microSignals?.return_1h_percent || 0) >= 0 ? '+' : ''}{microSignals?.return_1h_percent}%
                    </div>
                  </div>
                  <div className="p-2 bg-slate-950/50 rounded-lg border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase">Retur 2-Jam</div>
                    <div className={`text-xs font-bold ${
                      (microSignals?.return_2h_percent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {(microSignals?.return_2h_percent || 0) >= 0 ? '+' : ''}{microSignals?.return_2h_percent}%
                    </div>
                  </div>
                  <div className="p-2 bg-slate-950/50 rounded-lg border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase">Retur 3-Jam</div>
                    <div className={`text-xs font-bold ${
                      (microSignals?.return_3h_percent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {(microSignals?.return_3h_percent || 0) >= 0 ? '+' : ''}{microSignals?.return_3h_percent}%
                    </div>
                  </div>
                  <div className="p-2 bg-slate-950/50 rounded-lg border border-slate-800">
                    <div className="text-[9px] text-slate-500 uppercase">Retur 6-Jam</div>
                    <div className={`text-xs font-bold ${
                      (microSignals?.return_6h_percent || 0) >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {(microSignals?.return_6h_percent || 0) >= 0 ? '+' : ''}{microSignals?.return_6h_percent}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Daily Bulk News Scraping & Sentiment Card (Col 6) */}
            <div className="lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center space-x-2">
                    <Newspaper className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-mono font-bold text-white uppercase tracking-wider">
                      Sentimen Scraping Massal Berita Harian
                    </span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      newsSentiment?.source_type === 'EMITEN_LANGSUNG'
                        ? 'bg-cyan-950/60 text-cyan-300 border-cyan-800/60'
                        : 'bg-purple-950/60 text-purple-300 border-purple-800/60'
                    }`}>
                      {newsSentiment?.source_description || 'Sentimen Terkait'}
                    </span>
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded">
                      {newsSentiment?.article_count || 0} Artikel
                    </span>
                  </div>
                </div>

                {/* Sentiment Score Gauge */}
                <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-xl flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="text-[10px] font-mono text-slate-400 uppercase">Skor Sentimen Berita Harian</div>
                    <div className="flex items-baseline space-x-2">
                      <span className={`text-2xl font-black font-mono ${
                        (newsSentiment?.sentiment_score || 0) > 0.05 ? 'text-emerald-400' :
                        (newsSentiment?.sentiment_score || 0) < -0.05 ? 'text-rose-400' : 'text-slate-300'
                      }`}>
                        {(newsSentiment?.sentiment_score || 0) > 0 ? '+' : ''}{newsSentiment?.sentiment_score}
                      </span>
                      <span className="text-xs font-mono text-slate-500">Skala -1.0 s/d +1.0</span>
                    </div>
                  </div>

                  <div className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold border ${
                    newsSentiment?.label === 'BULLISH' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
                    newsSentiment?.label === 'BEARISH' ? 'bg-rose-500/20 text-rose-300 border-rose-500/30' :
                    'bg-slate-800 text-slate-300 border-slate-700'
                  }`}>
                    {newsSentiment?.label || 'NEUTRAL'}
                  </div>
                </div>

                {/* Scraped Headline Stream */}
                <div className="space-y-2">
                  <div className="text-[11px] font-mono text-slate-400">Headline Berita Terkini Hasil Scraping:</div>
                  <div className="space-y-2 max-h-[170px] overflow-y-auto pr-1">
                    {newsSentiment?.recent_headlines && newsSentiment.recent_headlines.length > 0 ? (
                      newsSentiment.recent_headlines.map((hl, idx) => (
                        <div key={idx} className="p-2.5 bg-slate-950/40 hover:bg-slate-950/80 rounded-xl border border-slate-800/80 flex items-start space-x-2 text-xs transition-colors">
                          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-1.5 shrink-0" />
                          <div className="flex-1 space-y-1">
                            <div className="text-slate-200 font-sans leading-snug line-clamp-2">{hl.title}</div>
                            <div className="flex items-center space-x-2 text-[10px] font-mono text-slate-500">
                              <span>{hl.source || 'Media Finansial'}</span>
                              <span>|</span>
                              <span className={`font-bold ${
                                (hl.sentiment_score || 0) > 0 ? 'text-emerald-400' :
                                (hl.sentiment_score || 0) < 0 ? 'text-rose-400' : 'text-slate-400'
                              }`}>
                                Sentimen: {hl.sentiment_score}
                              </span>
                            </div>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="p-4 text-xs font-mono text-slate-500 text-center bg-slate-950/30 rounded-xl">
                        Belum ada berita spesifik untuk aset ini di feed hari ini. Silakan klik tombol "Scrape Berita Harian".
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 text-[11px] font-mono text-slate-500 flex items-center justify-between">
                <span>Multi-Feed RSS: IDX, Finansial Nasional, Coindesk, Fed Macro</span>
                <span className="text-cyan-400 font-bold">11 Saluran Terpantau</span>
              </div>
            </div>
          </div>

          {/* Tertiary Bento Row: 7-Day Backtest Realization Log & Evaluation Track Record */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-3">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                    Rekam Jejak Evaluasi Backtest 7 Hari (168 Bar per Jam)
                  </h3>
                </div>
                <p className="text-xs text-slate-400">
                  Pengujian validasi walk-forward historis pada setiap bar penutupan 1 jam untuk memverifikasi realisasi aktual 3 jam ke depan.
                </p>
              </div>

              {/* Accuracy Badge */}
              <div className="flex items-center space-x-3 bg-slate-950 p-2 rounded-xl border border-slate-800 font-mono">
                <div className="text-right">
                  <div className="text-[10px] text-slate-400 uppercase">Akurasi 7 Hari (3H)</div>
                  <div className="text-base font-black text-emerald-400">
                    {backtest?.accuracy_percent || 0}%
                  </div>
                </div>
                <div className="text-xs text-slate-500 border-l border-slate-800 pl-3">
                  <div>{backtest?.correct_predictions || 0} / {backtest?.evaluated_bars || 0} Benar</div>
                  <div className="text-[10px] text-slate-400">Bar Teruji</div>
                </div>
              </div>
            </div>

            {/* Realization Log Table */}
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-800/80 text-left">
                    <th className="pb-2.5 font-bold uppercase tracking-wider">Waktu Bar Teruji</th>
                    <th className="pb-2.5 font-bold uppercase tracking-wider">Harga Pada Waktu t</th>
                    <th className="pb-2.5 font-bold uppercase tracking-wider">Prediksi Model</th>
                    <th className="pb-2.5 font-bold uppercase tracking-wider">Realisasi Aktual (t+3 Jam)</th>
                    <th className="pb-2.5 font-bold uppercase tracking-wider text-right">Hasil Evaluasi</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {backtest?.recent_eval_log && backtest.recent_eval_log.length > 0 ? (
                    backtest.recent_eval_log.map((log, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 text-slate-300 flex items-center space-x-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>{log.time}</span>
                        </td>
                        <td className="py-2.5 text-white font-bold">
                          {log.price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.predicted === 'NAIK' 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                              : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                          }`}>
                            {log.predicted}
                          </span>
                        </td>
                        <td className="py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            log.actual === 'NAIK' 
                              ? 'bg-emerald-950/60 text-emerald-400' 
                              : 'bg-rose-950/60 text-rose-400'
                          }`}>
                            {log.actual}
                          </span>
                        </td>
                        <td className="py-2.5 text-right">
                          {log.is_correct ? (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                              <CheckCircle2 className="w-3 h-3" />
                              <span>BENAR</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                              <XCircle className="w-3 h-3" />
                              <span>MELESET</span>
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="py-6 text-center text-slate-500 font-mono">
                        Data evaluasi backtest 7 hari sedang diproses...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="pt-2 flex items-center justify-between text-[11px] font-mono text-slate-500 border-t border-slate-800">
              <span className="flex items-center space-x-1.5">
                <Database className="w-3.5 h-3.5 text-slate-400" />
                <span>Validasi Berkelanjutan Walk-Forward 7 Hari Terakhir</span>
              </span>
              <span>Ensemble: Random Forest 150 + HistGradientBoosting 100</span>
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
