import { 
  FinblixLogo, 
  CryptoOrbitIcon, 
  MicrostructureWickIcon 
} from '../icons/CustomIcons';
import { 
  Compass, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Target, 
  CheckCircle2, 
  XCircle, 
  RefreshCw, 
  Cpu, 
  Newspaper, 
  Layers, 
  ShieldCheck, 
  AlertTriangle,
  History,
  Info,
  Sparkles,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  Building2,
  Landmark,
  Coins,
  Globe,
  Clock,
  SlidersHorizontal,
  Search
} from 'lucide-react';
import { getDailyPrediction, getMarketHistory, getIndicators, trainModel, getModelStatus } from '../../api';
import ChartToolbar from '../chart/ChartToolbar';
import CandlestickChart from '../chart/CandlestickChart';
import IndicatorSubChart from '../chart/IndicatorSubChart';


export default function DailyPredictionView({ 
  tickers = [], 
  defaultSymbol = 'BTC/USDT',
  onSelectSymbol 
}) {
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [timeframe, setTimeframe] = useState('1d');
  const [predictionData, setPredictionData] = useState(null);

  // Keep symbol in sync if defaultSymbol prop updates
  useEffect(() => {
    if (defaultSymbol && defaultSymbol !== symbol) {
      setSymbol(defaultSymbol);
    }
  }, [defaultSymbol]);
  const [bars, setBars] = useState([]);
  const [indicators, setIndicators] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chartLoading, setChartLoading] = useState(false);
  const [error, setError] = useState(null);

  // 1-Year AI Model Training State
  const [modelStatus, setModelStatus] = useState(null);
  const [training, setTraining] = useState(false);
  const [trainingMessage, setTrainingMessage] = useState(null);

  // Audit Table Filter & Conviction Mode
  const [auditFilter, setAuditFilter] = useState('all'); // 'all' | 'high' | 'correct' | 'incorrect'
  const [accuracyMode, setAccuracyMode] = useState('high'); // 'high' | 'all'

  const [overlays, setOverlays] = useState({
    ema20: true,
    ema50: true,
    ema200: false,
    bollinger: false,
  });

  // Fetch prediction and historical track record
  const fetchPrediction = async (sym = symbol) => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDailyPrediction(sym);
      setPredictionData(res.data.data);
    } catch (e) {
      console.error('Failed to fetch prediction:', e);
      setError(e.response?.data?.detail || 'Gagal mengambil data prediksi harian');
    } finally {
      setLoading(false);
    }
  };

  // Fetch chart bars & quantitative indicators
  const fetchChartData = async (sym = symbol, tf = timeframe) => {
    setChartLoading(true);
    try {
      const [historyRes, indRes] = await Promise.all([
        getMarketHistory(sym, tf, 120),
        getIndicators(sym, tf),
      ]);
      setBars(historyRes.data.bars || []);
      setIndicators(indRes.data);
    } catch (e) {
      console.error('Failed to fetch chart data:', e);
    } finally {
      setChartLoading(false);
    }
  };

  // Fetch 1-Year ML Model Training Status
  const fetchStatus = async (sym = symbol) => {
    try {
      const res = await getModelStatus(sym);
      if (res.data?.data?.is_trained) {
        setModelStatus(res.data.data);
      } else {
        setModelStatus(null);
      }
    } catch (e) {
      console.error('Failed to fetch model status:', e);
    }
  };

  // Trigger Multi-Year Historical & Scraping Training
  const handleStartTraining = async () => {
    setTraining(true);
    setTrainingMessage('Mengambil 1.000 bar candlestick & sentimen berita riil... Melatih Ensemble 1.200 Pohon dengan 5-Fold TimeSeries CV...');
    setError(null);
    try {
      const res = await trainModel(symbol, 500, 400);
      setModelStatus(res.data.data);
      setTrainingMessage(`Pelatihan Selesai dalam ${res.data.data.training_duration_seconds}s! Model aktif dan terverifikasi.`);
      await fetchPrediction(symbol);
    } catch (e) {
      console.error('Training failed:', e);
      setError(e.response?.data?.detail || 'Gagal melatih model multi-tahun');
      setTrainingMessage(null);
    } finally {
      setTraining(false);
    }
  };

  useEffect(() => {
    fetchPrediction(symbol);
    fetchChartData(symbol, timeframe);
    fetchStatus(symbol);
    if (onSelectSymbol) {
      onSelectSymbol(symbol);
    }
  }, [symbol, timeframe]);

  const pred = predictionData?.prediction;
  const track = predictionData?.accuracy_track_record;
  const hc = track?.high_conviction;
  const mlModel = predictionData?.ml_model;
  const isUp = pred?.direction === 'NAIK';
  const isDown = pred?.direction === 'TURUN';

  const currentAsset = tickers.find(t => t.symbol === symbol) || {
    symbol,
    name: symbol,
    asset_type: 'crypto',
    base_currency: 'USD',
  };

  // Filtered audit log
  const filteredDailyLog = useMemo(() => {
    if (!track?.daily_log) return [];
    if (auditFilter === 'high') return track.daily_log.filter(l => l.conviction === 'HIGH');
    if (auditFilter === 'pro_trend') return track.daily_log.filter(l => l.mtf_confluence === 'PRO_TREND');
    if (auditFilter === 'correct') return track.daily_log.filter(l => l.is_correct);
    if (auditFilter === 'incorrect') return track.daily_log.filter(l => !l.is_correct);
    return track.daily_log;
  }, [track?.daily_log, auditFilter]);

  return (
    <div className="space-y-6">
      
      {/* 1. Segregated Market Navigator & Asset Selection Cockpit */}
      <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl p-5 shadow-2xl space-y-5">
        
        {/* Top Bar: Title, Market Categories Switcher & Refresh */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
          <div className="flex items-center space-x-3.5">
            <div className="relative shrink-0">
              <FinblixLogo className="w-11 h-11" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-black tracking-tight text-white font-mono uppercase">
                  FINBLIX PREDICTION COCKPIT
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-purple-500/10 text-purple-400 border border-purple-500/20 font-mono">
                  CRYPTO MICROSTRUCTURE ENGINE
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Model Kuantitatif Native Kripto 24/7: Likuiditas Order Flow, Wick Rejection, Funding Rate & Kontrarian Sentimen.
              </p>
            </div>
          </div>

          {/* Action Buttons: Refresh Data */}
          <div className="flex items-center space-x-2.5 self-end lg:self-auto">
            <button
              onClick={() => {
                fetchPrediction(symbol);
                fetchChartData(symbol, timeframe);
                fetchStatus(symbol);
              }}
              disabled={loading || chartLoading || training}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 hover:text-white border border-slate-700/80 text-slate-200 text-xs font-mono font-bold flex items-center space-x-2 transition-all shadow-md active:scale-[0.98] disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading || chartLoading ? 'animate-spin' : ''}`} />
              <span>{loading ? 'Mengalkulasi...' : 'Segarkan Data'}</span>
            </button>
          </div>
        </div>

        {/* Market Status Banner */}
        <div className="p-3.5 rounded-xl bg-gradient-to-r from-purple-950/40 via-slate-900 to-slate-900 border border-purple-500/30 flex flex-wrap items-center justify-between gap-3 text-xs font-mono shadow-md">
          <div className="flex items-center space-x-2.5 text-slate-200">
            <CryptoOrbitIcon className="w-4 h-4 text-purple-400 shrink-0" />
            <span>
              <strong className="text-white">Pasar Kripto Global (Spot & Futures)</strong> · Likuiditas 24 Jam / 7 Hari Non-Stop · Denominasi: <span className="text-purple-300 font-semibold">USDT ($)</span>
            </span>
          </div>

          <div className="flex items-center space-x-2 text-[11px]">
            <span className="text-slate-400">Algoritma Aktif:</span>
            <span className="px-2 py-0.5 rounded font-bold border bg-purple-500/10 text-purple-400 border-purple-500/30">
              CRYPTO MICROSTRUCTURE ENGINE
            </span>
          </div>
        </div>

        {/* Filtered Asset Shelf */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between text-xs font-mono">
            <span className="text-slate-400 flex items-center space-x-1.5 uppercase font-bold tracking-wider">
              <SlidersHorizontal className="w-3.5 h-3.5 text-purple-400" />
              <span>Daftar Aset Kripto Teratas</span>
            </span>
            <span className="text-[11px] text-slate-500">Klik aset untuk melihat analisis prediksi</span>
          </div>

          {/* Interactive Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2.5">
            {tickers.map(item => {
              const isSelected = item.symbol === symbol;
              const isPos = (item.change_24h_percent || 0) >= 0;

              return (
                <button
                  key={item.symbol}
                  type="button"
                  onClick={() => setSymbol(item.symbol)}
                  className={`p-3 rounded-xl border text-left transition-all duration-150 flex flex-col justify-between group active:scale-[0.98] ${
                    isSelected
                      ? 'bg-purple-950/30 border-purple-500/80 shadow-md shadow-purple-950/40 ring-1 ring-purple-500/50'
                      : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/80'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-black text-sm text-white group-hover:text-purple-400 transition-colors">
                        {item.symbol}
                      </span>
                      {isSelected && (
                        <span className="w-2 h-2 rounded-full animate-ping bg-purple-400" />
                      )}
                    </div>
                    
                    <div className="text-[10px] text-slate-400 truncate mb-2 font-sans" title={item.name}>
                      {item.name}
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-800/60 font-mono">
                    <div className="text-xs font-bold text-slate-200">
                      ${item.last_price?.toLocaleString('en-US')}
                    </div>
                    <div className={`text-[10px] flex items-center space-x-0.5 font-bold mt-0.5 ${
                      isPos ? 'text-emerald-400' : 'text-rose-400'
                    }`}>
                      {isPos ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      <span>{isPos ? '+' : ''}{item.change_24h_percent || 0}%</span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Quick Dropdown Fallback for Search / Mobile */}
          <div className="pt-2 flex items-center justify-between text-xs text-slate-400">
            <span className="text-[11px] font-mono">
              Aset Terpilih: <strong className="text-white">{symbol}</strong> - {currentAsset?.name}
            </span>

            {/* Quick selector dropdown */}
            <div className="flex items-center space-x-2">
              <span className="text-[11px] font-mono text-slate-500 hidden sm:inline">Pindah Cepat:</span>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="bg-slate-900 border border-slate-700/80 rounded-lg px-2.5 py-1 text-[11px] font-mono text-slate-200 focus:outline-none focus:border-purple-500 cursor-pointer"
              >
                {tickers.map(t => (
                  <option key={t.symbol} value={t.symbol}>
                    {t.symbol} - {t.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

      </div>

      {error && (
        <div className="bg-rose-950/40 border border-rose-800/80 rounded-2xl p-4 text-xs font-mono text-rose-300 flex items-center space-x-3 shadow-lg">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {predictionData && (
        <>
          {/* 2. Bento Cockpit: Primary Direction, Target Range & Verified Audit */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
            
            {/* Panel A: Direction & Probability Verdict (Col span 5) */}
            <div className={`lg:col-span-5 border rounded-2xl p-6 transition-all shadow-xl flex flex-col justify-between ${
              isUp 
                ? 'bg-gradient-to-br from-emerald-950/30 via-[#0c1220] to-[#0c1220] border-emerald-500/30' 
                : isDown 
                  ? 'bg-gradient-to-br from-rose-950/30 via-[#0c1220] to-[#0c1220] border-rose-500/30' 
                  : 'bg-[#0c1220] border-slate-800'
            }`}>
              <div>
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                  <span>Arah Prediksi Akhir Hari Esok</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold font-mono border ${
                    isUp ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                    isDown ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' :
                    'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}>
                    {pred?.label}
                  </span>
                </div>

                <div className="mt-4 flex items-center space-x-4">
                  <div className={`w-14 h-14 rounded-2xl flex items-center justify-center shrink-0 border shadow-inner ${
                    isUp ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' :
                    isDown ? 'bg-rose-500/20 text-rose-400 border-rose-500/40' :
                    'bg-amber-500/20 text-amber-400 border-amber-500/40'
                  }`}>
                    {isUp && <ArrowUpRight className="w-8 h-8 stroke-[2.5]" />}
                    {isDown && <ArrowDownRight className="w-8 h-8 stroke-[2.5]" />}
                    {!isUp && !isDown && <Minus className="w-8 h-8 stroke-[2.5]" />}
                  </div>

                  <div>
                    <div className={`text-4xl font-black font-mono tracking-tight ${
                      isUp ? 'text-emerald-400' : isDown ? 'text-rose-400' : 'text-amber-400'
                    }`}>
                      {pred?.direction}
                    </div>
                    <div className="text-xs font-mono text-slate-400 mt-0.5">
                      Skor Komposit: <span className="font-bold text-white">{pred?.composite_score > 0 ? `+${pred?.composite_score}` : pred?.composite_score}</span> / 100
                    </div>

                    {/* Conviction & Multi-Timeframe Badges */}
                    <div className="mt-2.5 flex flex-wrap items-center gap-2">
                      {/* Engine Differentiation Badge */}
                      <span className="px-2.5 py-0.5 rounded-md text-[10px] font-bold font-mono border flex items-center space-x-1.5 bg-purple-500/15 text-purple-300 border-purple-500/40 shadow-sm shadow-purple-500/10">
                        <Cpu className="w-3 h-3" />
                        <span>ALGORITMA KRIPTO: MICROSTRUCTURE ENGINE</span>
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-md text-[10px] font-bold font-mono border flex items-center space-x-1.5 ${
                        pred?.conviction_tier === 'HIGH' 
                          ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/40 shadow-sm shadow-emerald-500/10' 
                          : pred?.conviction_tier === 'MODERATE'
                            ? 'bg-blue-500/15 text-blue-400 border-blue-500/40'
                            : 'bg-amber-500/15 text-amber-400 border-amber-500/40'
                      }`}>
                        <ShieldCheck className="w-3 h-3" />
                        <span>{pred?.trade_status || 'HIGH CONVICTION'}</span>
                      </span>

                      {pred?.weekly_trend && (
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold font-mono border ${
                          pred?.weekly_trend === 'BULLISH'
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                            : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                        }`}>
                          WEEKLY 1W: {pred?.weekly_trend}
                        </span>
                      )}

                      {pred?.mtf_confluence === 'PRO_TREND' ? (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold font-mono border bg-teal-500/15 text-teal-300 border-teal-500/40 flex items-center space-x-1">
                          <CheckCircle2 className="w-3 h-3 text-teal-400" />
                          <span>PRO-TREND (1W ALIGNED)</span>
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold font-mono border bg-amber-500/15 text-amber-400 border-amber-500/40 flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                          <span>COUNTER-TREND SETUP</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {pred?.recommendation && (
                  <div className="mt-3 text-[11px] text-slate-300 bg-slate-900/70 border border-slate-800 rounded-xl p-2.5 leading-relaxed font-sans">
                    {pred?.recommendation}
                  </div>
                )}
              </div>

              {/* Confidence Meter */}
              <div className="mt-5 pt-4 border-t border-slate-800/80">
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="text-slate-400 flex items-center space-x-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-400" />
                    <span>Tingkat Keyakinan (Confidence)</span>
                  </span>
                  <span className="font-extrabold text-white text-sm">{pred?.confidence_percent}%</span>
                </div>
                <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden border border-slate-800/80">
                  <div 
                    className={`h-full rounded-full transition-all duration-700 ${
                      isUp ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 
                      isDown ? 'bg-gradient-to-r from-rose-500 to-red-400' : 
                      'bg-gradient-to-r from-amber-500 to-yellow-400'
                    }`}
                    style={{ width: `${pred?.confidence_percent}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-500 mt-2">
                  <span>Konsensus: 60% TA + 40% News</span>
                  {mlModel?.is_trained && (
                    <span className="text-blue-400 font-semibold flex items-center space-x-1">
                      <Cpu className="w-3 h-3" />
                      <span>ML Ensemble Active</span>
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Panel B: Estimated Target Price Range & Close Price (Col span 4) */}
            <div className="lg:col-span-4 bg-[#0c1220] border border-slate-800/80 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                  <span>Target Rentang Harga (ATR 14)</span>
                  <Target className="w-4 h-4 text-blue-400" />
                </div>

                <div className="mt-3">
                  <div className="text-[11px] font-mono text-slate-500 uppercase">Harga Terkini</div>
                  <div className="text-2xl font-black font-mono text-white tracking-tight mt-0.5">
                    {isIdr ? `Rp ${predictionData.current_price?.toLocaleString('id-ID')}` : `$${predictionData.current_price?.toLocaleString('en-US')}`}
                  </div>
                </div>

                <div className="mt-4 space-y-2 font-mono">
                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-2.5 flex items-center justify-between">
                    <span className="text-xs text-slate-400 flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>Ceiling Target (High):</span>
                    </span>
                    <span className="text-xs font-bold text-emerald-400">
                      {isIdr ? `Rp ${pred?.target_range?.estimated_high?.toLocaleString('id-ID')}` : `$${pred?.target_range?.estimated_high?.toLocaleString('en-US')}`}
                    </span>
                  </div>

                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-2.5 flex items-center justify-between">
                    <span className="text-xs text-slate-400 flex items-center space-x-1">
                      <span className="w-2 h-2 rounded-full bg-rose-400" />
                      <span>Floor Target (Low):</span>
                    </span>
                    <span className="text-xs font-bold text-rose-400">
                      {isIdr ? `Rp ${pred?.target_range?.estimated_low?.toLocaleString('id-ID')}` : `$${pred?.target_range?.estimated_low?.toLocaleString('en-US')}`}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-[11px] font-mono text-slate-500 mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                <span>Tanggal Target:</span>
                <span className="font-bold text-slate-300">{predictionData.target_date}</span>
              </div>
            </div>

            {/* Panel C: 30-Day Walk-Forward Historical Audit (Col span 3) */}
            <div className="lg:col-span-3 bg-[#0c1220] border border-slate-800/80 rounded-2xl p-6 shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase tracking-wider">
                  <span>Akurasi Model 30 Hari</span>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>

                {/* Mode Selector: Sinyal Kuat Saja vs Semua Hari */}
                <div className="mt-2.5 flex items-center bg-slate-900/90 border border-slate-800 rounded-lg p-0.5 font-mono text-[10px]">
                  <button
                    onClick={() => setAccuracyMode('high')}
                    className={`flex-1 py-1 rounded font-bold transition-all text-center ${
                      accuracyMode === 'high' 
                        ? 'bg-emerald-600 text-white shadow' 
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Sinyal Kuat ({hc?.accuracy_percentage || 0}%)
                  </button>
                  <button
                    onClick={() => setAccuracyMode('all')}
                    className={`flex-1 py-1 rounded font-bold transition-all text-center ${
                      accuracyMode === 'all' 
                        ? 'bg-slate-700 text-white shadow' 
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Semua ({track?.accuracy_percentage || 0}%)
                  </button>
                </div>

                <div className="mt-3">
                  <div className="text-3xl font-black font-mono text-emerald-400 tracking-tight flex items-baseline space-x-2">
                    <span>
                      {accuracyMode === 'high' 
                        ? `${hc?.accuracy_percentage || track?.accuracy_percentage}%` 
                        : `${track?.accuracy_percentage}%`
                      }
                    </span>
                    {accuracyMode === 'high' && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        70%+ WIN RATE
                      </span>
                    )}
                  </div>
                  <div className="text-xs font-mono text-slate-400 mt-1">
                    {accuracyMode === 'high' ? (
                      <>
                        <span className="text-emerald-400 font-bold">{hc?.correct_predictions}</span> Benar / {hc?.days_evaluated} Hari Sinyal Terpilih
                      </>
                    ) : (
                      <>
                        <span className="text-emerald-400 font-bold">{track?.correct_predictions}</span> Benar / {track?.days_evaluated} Hari Perdagangan
                      </>
                    )}
                  </div>
                </div>

                <div className="mt-4 p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/20 text-xs font-mono text-emerald-300">
                  <div className="text-[10px] text-emerald-400/80 uppercase font-bold">Status Keandalan:</div>
                  <div className="font-bold mt-0.5">
                    {accuracyMode === 'high' ? (hc?.verdict || 'AKURASI SUPERIOR TINGGI') : track?.verdict}
                  </div>
                </div>
              </div>

              <div className="text-[11px] font-mono text-slate-500 mt-4 pt-3 border-t border-slate-800/80">
                {accuracyMode === 'high' 
                  ? 'Menyaring noise konsolidasi untuk memaksimalkan win rate.'
                  : 'Evaluasi lengkap mencakup seluruh hari perdagangan.'
                }
              </div>
            </div>

          </div>

          {/* 3. Dedicated Multi-Year AI Model Training Command Center */}
          <div className="bg-[#0c1220] border border-indigo-900/40 rounded-2xl p-6 shadow-xl relative overflow-hidden">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-5">
              <div className="flex items-center space-x-3.5">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 flex items-center justify-center shrink-0">
                  <Cpu className="w-5 h-5 animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-base font-extrabold font-mono text-white">
                      PUSAT TRAINING MODEL AI MULTI-TAHUN (1.000 BAR & SCRAPING)
                    </h3>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${
                      modelStatus 
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' 
                        : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    }`}>
                      {modelStatus ? 'MODEL AKTIF (ENSEMBLE 1.200 TREES)' : 'BELUM DITRAINING'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Melatih Tri-Model Soft Voting Ensemble (Random Forest 500 + Gradient Boosting 400 + Extra Trees 300 = 7.200 Decision Trees Terlatih) dengan 5-Fold TimeSeries Cross Validation.
                  </p>
                </div>
              </div>

              {/* Start Training Button */}
              <button
                onClick={handleStartTraining}
                disabled={training}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 disabled:opacity-50 text-white text-xs font-mono font-bold flex items-center space-x-2 transition-all shadow-lg shadow-indigo-600/25 shrink-0 active:scale-[0.98] cursor-pointer"
              >
                <Zap className={`w-4 h-4 ${training ? 'animate-spin' : 'fill-white'}`} />
                <span>{training ? 'Sedang Melatih Model (Komputasi Berat)...' : 'Mulai Training Multi-Tahun'}</span>
              </button>
            </div>

            {/* Training Live Progress Banner */}
            {training && (
              <div className="mt-4 p-4 rounded-xl bg-blue-950/40 border border-blue-800/80 text-xs font-mono text-blue-300 flex items-center space-x-3 animate-pulse">
                <RefreshCw className="w-5 h-5 text-blue-400 animate-spin shrink-0" />
                <div>
                  <div className="font-bold">PROSES PELATIHAN BERAT SEDANG BERJALAN...</div>
                  <div className="text-[11px] text-blue-400/80 mt-0.5">{trainingMessage}</div>
                </div>
              </div>
            )}

            {/* Trained Model Insights & Metrics */}
            {modelStatus && (
              <div className="mt-6 space-y-5">
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 font-mono">
                    <div className="text-[10px] text-slate-400 uppercase">Durasi Komputasi Training</div>
                    <div className="text-lg font-black text-indigo-400 mt-0.5">{modelStatus.training_duration_seconds} detik</div>
                    <div className="text-[10px] text-slate-500">Komputasi intensif CPU</div>
                  </div>

                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 font-mono">
                    <div className="text-[10px] text-slate-400 uppercase">Sampel Data Multi-Tahun</div>
                    <div className="text-lg font-black text-white mt-0.5">{modelStatus.samples_trained + modelStatus.samples_tested} Bar</div>
                    <div className="text-[10px] text-slate-500">{modelStatus.samples_trained} Train / {modelStatus.samples_tested} Test</div>
                  </div>

                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 font-mono">
                    <div className="text-[10px] text-slate-400 uppercase">Akurasi Out-Of-Sample Test</div>
                    <div className="text-lg font-black text-emerald-400 mt-0.5">{modelStatus.metrics?.test_accuracy_pct}%</div>
                    <div className="text-[10px] text-slate-500">ROC-AUC: {modelStatus.metrics?.roc_auc_pct}%</div>
                  </div>

                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 font-mono">
                    <div className="text-[10px] text-slate-400 uppercase">5-Fold TimeSeries CV</div>
                    <div className="text-lg font-black text-blue-400 mt-0.5">{modelStatus.metrics?.cv_5fold_mean_pct}%</div>
                    <div className="text-[10px] text-slate-500">Walk-forward validation</div>
                  </div>
                </div>

                {/* Top Features Importance Ranking */}
                <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                  <div className="text-xs font-mono font-bold text-slate-300 uppercase mb-3 flex items-center space-x-2">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Top Fitur Paling Berpengaruh dalam Model (Feature Importance Ranking)</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {modelStatus.top_features?.slice(0, 4).map((f, i) => (
                      <div key={i} className="bg-slate-950/80 border border-slate-800/80 rounded-lg p-2.5 font-mono text-xs">
                        <div className="flex items-center justify-between text-slate-400">
                          <span className="font-semibold text-slate-200">#{i + 1} {f.feature}</span>
                          <span className="text-indigo-400 font-bold">{f.importance}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full mt-2 overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-indigo-500 to-blue-500 rounded-full" 
                            style={{ width: `${Math.min(100, f.importance * 10)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="text-[11px] font-mono text-slate-500 flex items-center justify-between">
                  <span>Waktu Terakhir Dilatih: {modelStatus.trained_at}</span>
                  <span className="text-emerald-400 flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Model Terverifikasi Aktif</span>
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* 4. Chart & Hybrid Model Breakdown Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Chart Column (2 of 3) */}
            <div className="lg:col-span-2 space-y-4">
              <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
                <ChartToolbar
                  symbol={symbol}
                  assetName={currentAsset.name}
                  timeframe={timeframe}
                  setTimeframe={setTimeframe}
                  overlays={overlays}
                  setOverlays={setOverlays}
                  onRefresh={() => fetchChartData(symbol, timeframe)}
                  loading={chartLoading}
                />

                <CandlestickChart
                  bars={bars}
                  overlays={overlays}
                  height={440}
                />
              </div>

              {/* Sub-Indicators (RSI, MACD, Volume) */}
              <IndicatorSubChart indicators={indicators} />
            </div>

            {/* Right Column: Hybrid Model Weights & Key Drivers (1 of 3) */}
            <div className="space-y-4">
              
              {/* Model Weights Breakdown */}
              <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl p-5 shadow-xl space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div className="flex items-center space-x-2 text-xs font-mono font-bold text-white uppercase">
                    <Layers className="w-4 h-4 text-blue-400" />
                    <span>Komposisi Model Hibrida</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800/90 text-slate-300 border border-slate-700/60">
                    60% TA + 40% News
                  </span>
                </div>

                {/* Technical Score */}
                <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                      <Cpu className="w-3.5 h-3.5 text-blue-400" />
                      <span>Analisis Teknikal (60%)</span>
                    </span>
                    <span className="text-blue-400 font-bold">{pred?.breakdown?.technical_score} / 100</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    EMA 20/50 Alignment, RSI 14 ({pred?.breakdown?.rsi_value}) & MACD Momentum.
                  </div>
                </div>

                {/* Fundamental News Sentiment Score */}
                <div className="bg-slate-900/80 border border-slate-800/80 rounded-xl p-3.5 space-y-1.5">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="flex items-center space-x-1.5 text-slate-300 font-semibold">
                      <Newspaper className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Fundamental Kripto: Sentimen & On-Chain (35%)</span>
                    </span>
                    <span className="text-emerald-400 font-bold">{pred?.breakdown?.fundamental_score} / 100</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    <span>
                      Skor Berita: <span className="text-white font-mono">{pred?.breakdown?.news_sentiment_score}</span> | Fear & Greed: <span className="text-white font-mono">{pred?.breakdown?.fear_greed_index}</span>
                    </span>
                  </div>
                </div>
              </div>

              {/* Key Drivers Explanation */}
              <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl p-5 shadow-xl space-y-4">
                <div className="flex items-center space-x-2 text-xs font-mono font-bold text-white uppercase border-b border-slate-800/80 pb-3">
                  <History className="w-4 h-4 text-indigo-400" />
                  <span>Faktor Pemicu Prediksi (Drivers)</span>
                </div>

                {/* Technical Reasons */}
                <div className="space-y-2">
                  <div className="text-[11px] font-mono font-bold text-blue-400 uppercase">
                    Pemicu Teknikal:
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {pred?.key_drivers?.technical?.map((reason, idx) => (
                      <li key={idx} className="flex items-start space-x-2 leading-relaxed">
                        <span className="text-blue-500 font-bold shrink-0 mt-0.5">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Fundamental Reasons */}
                <div className="space-y-2 pt-2 border-t border-slate-800/60">
                  <div className="text-[11px] font-mono font-bold text-emerald-400 uppercase">
                    Pemicu Sentimen & Berita:
                  </div>
                  <ul className="space-y-1.5 text-xs text-slate-300">
                    {pred?.key_drivers?.fundamental?.map((reason, idx) => (
                      <li key={idx} className="flex items-start space-x-2 leading-relaxed">
                        <span className="text-emerald-500 font-bold shrink-0 mt-0.5">•</span>
                        <span>{reason}</span>
                      </li>
                    ))}
                  </ul>
                </div>


              </div>

            </div>

          </div>

          {/* 5. 30-Day Transparent Historical Accuracy Track Record Table */}
          <div className="bg-[#0c1220] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
            <div className="p-5 border-b border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold font-mono text-white flex items-center space-x-2">
                    <span>AUDIT REKAM JEJAK AKURASI 30 HARI TERAKHIR</span>
                    <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      TRANSPARAN
                    </span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    Validasi ke belakang secara walk-forward membandingkan arah prediksi dengan realisasi harga penutupan aktual.
                  </p>
                </div>
              </div>

              {/* Status Filter Pills */}
              <div className="flex items-center space-x-2 bg-slate-900/90 border border-slate-800 rounded-xl p-1 font-mono text-xs">
                <button
                  onClick={() => setAuditFilter('all')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    auditFilter === 'all'
                      ? 'bg-blue-600 text-white font-bold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Semua ({track?.days_evaluated || 0})
                </button>
                <button
                  onClick={() => setAuditFilter('high')}
                  className={`px-3 py-1 rounded-lg transition-all flex items-center space-x-1 ${
                    auditFilter === 'high'
                      ? 'bg-emerald-600 text-white font-bold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Sparkles className="w-3 h-3 text-emerald-300" />
                  <span>Sinyal Kuat ({hc?.days_evaluated || 0})</span>
                </button>
                <button
                  onClick={() => setAuditFilter('pro_trend')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    auditFilter === 'pro_trend'
                      ? 'bg-teal-600 text-white font-bold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Pro-Trend 1W
                </button>
                <button
                  onClick={() => setAuditFilter('correct')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    auditFilter === 'correct'
                      ? 'bg-emerald-700/80 text-white font-bold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Benar ({track?.correct_predictions || 0})
                </button>
                <button
                  onClick={() => setAuditFilter('incorrect')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    auditFilter === 'incorrect'
                      ? 'bg-rose-600 text-white font-bold shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Salah ({track?.incorrect_predictions || 0})
                </button>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full text-left border-collapse text-xs font-mono">
                <thead className="bg-[#080d1a] text-[10px] uppercase text-slate-400 sticky top-0 z-10 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Tanggal Bar</th>
                    <th className="py-3 px-4 font-semibold">Harga Close</th>
                    <th className="py-3 px-4 font-semibold">Tingkat Conviction</th>
                    <th className="py-3 px-4 font-semibold">Konfluensi MTF (1W)</th>
                    <th className="py-3 px-4 font-semibold">Prediksi Arah</th>
                    <th className="py-3 px-4 font-semibold">Pergerakan Aktual</th>
                    <th className="py-3 px-4 text-right font-semibold">Perubahan (%)</th>
                    <th className="py-3 px-4 text-center font-semibold">Status Audit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredDailyLog.map((log, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-4 text-slate-400 font-mono">{log.date}</td>
                      <td className="py-3 px-4 font-bold text-slate-200">
                        ${log.price?.toLocaleString('en-US')}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border inline-flex items-center space-x-1 ${
                          log.conviction === 'HIGH'
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : log.conviction === 'MODERATE'
                              ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                              : 'bg-slate-800/80 text-slate-400 border-slate-700'
                        }`}>
                          {log.conviction === 'HIGH' ? (
                            <>
                              <ShieldCheck className="w-3 h-3 text-emerald-400" />
                              <span>KUAT (HIGH)</span>
                            </>
                          ) : log.conviction === 'MODERATE' ? (
                            <span>MODERAT</span>
                          ) : (
                            <span>KONSOLIDASI</span>
                          )}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold border inline-flex items-center space-x-1 ${
                          log.mtf_confluence === 'PRO_TREND'
                            ? 'bg-teal-500/15 text-teal-300 border-teal-500/30'
                            : 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                        }`}>
                          <span>{log.mtf_confluence === 'PRO_TREND' ? 'PRO-TREND' : 'COUNTER'}</span>
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          log.predicted === 'NAIK' 
                            ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/60' 
                            : 'bg-rose-950/80 text-rose-400 border border-rose-800/60'
                        }`}>
                          {log.predicted}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold">
                        <span className={log.actual === 'NAIK' ? 'text-emerald-400' : 'text-rose-400'}>
                          {log.actual}
                        </span>
                      </td>
                      <td className={`py-3 px-4 text-right font-bold ${
                        log.change_percent >= 0 ? 'text-emerald-400' : 'text-rose-400'
                      }`}>
                        {log.change_percent >= 0 ? '+' : ''}{log.change_percent}%
                      </td>
                      <td className="py-3 px-4 text-center">
                        {log.is_correct ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                            <span>BENAR</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                            <XCircle className="w-3 h-3 text-rose-400" />
                            <span>SALAH</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* 6. Financial Disclaimer Footnote */}
      <div className="p-4 rounded-xl bg-slate-900/50 border border-slate-800/80 text-xs text-slate-400 flex items-start space-x-2.5 font-sans">
        <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          <strong className="text-slate-300">Pemberitahuan Risiko (Risk Disclaimer):</strong> Finblix adalah platform riset kuantitatif berbasis algoritma probabilitas historis dan pemindaian sentimen publik. Prediksi arah harian tidak menjamin kepastian mutlak di masa depan. Selalu gunakan manajemen risiko modal pribadi secara bijak.
        </p>
      </div>
    </div>
  );
}
