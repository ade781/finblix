import React, { useEffect, useState } from 'react';
import Navbar from './components/layout/Navbar';
import DailyPredictionView from './components/prediction/DailyPredictionView';
import ThreeHourPredictionView from './components/prediction/ThreeHourPredictionView';
import ScreenerTable from './components/screener/ScreenerTable';
import NewsView from './components/news/NewsView';
import AlertsModal from './components/alerts/AlertsModal';
import { getTickers, getAlerts } from './api';
import { Database, Server, Compass, ShieldCheck } from 'lucide-react';

export default function App() {
  // DASHBOARD UTAMA ADALAH PREDIKSI
  const [activeTab, setActiveTab] = useState('prediction');
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [tickers, setTickers] = useState([]);
  const [showAlertsModal, setShowAlertsModal] = useState(false);
  const [alertsCount, setAlertsCount] = useState(0);

  // Fetch list of tickers (Crypto & Stocks)
  const loadTickers = async () => {
    try {
      const res = await getTickers();
      setTickers(res.data.data || []);
    } catch (e) {
      console.error('Failed to load tickers:', e);
    }
  };

  // Fetch unread anomaly alerts
  const loadAlertsCount = async () => {
    try {
      const res = await getAlerts(true);
      setAlertsCount(res.data.count || 0);
    } catch (e) {
      console.error('Failed to load alerts count:', e);
    }
  };

  useEffect(() => {
    loadTickers();
    loadAlertsCount();
  }, []);

  const handleSelectFromScreener = (sym) => {
    setSelectedSymbol(sym);
    setActiveTab('prediction');
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedSymbol={selectedSymbol}
        setSelectedSymbol={setSelectedSymbol}
        tickers={tickers}
        onOpenAlerts={() => setShowAlertsModal(true)}
        alertsCount={alertsCount}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* DASHBOARD UTAMA: PREDIKSI HARIAN HIBRIDA */}
        {activeTab === 'prediction' && (
          <DailyPredictionView
            tickers={tickers}
            defaultSymbol={selectedSymbol}
            onSelectSymbol={setSelectedSymbol}
          />
        )}

        {/* HALAMAN KHUSUS: PREDIKSI 3 JAM KE DEPAN (TRAINING 7 HARI + SCRAPING HARIAN MASSAL) */}
        {activeTab === 'three-hours' && (
          <ThreeHourPredictionView
            tickers={tickers}
            defaultSymbol={selectedSymbol}
          />
        )}

        {/* SCREENER PREDIKSI PASAR */}
        {activeTab === 'screener' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold tracking-tight text-white font-mono flex items-center space-x-2">
                  <span>SCREENER PREDIKSI PASAR</span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    MULTI-ASET
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  Pantau sinyal teknikal dan buka dashboard prediksi instan untuk setiap aset kripto maupun saham.
                </p>
              </div>
            </div>

            <ScreenerTable
              tickers={tickers}
              onSelectAsset={handleSelectFromScreener}
            />
          </div>
        )}

        {/* SENTIMEN & BERITA HASIL SCRAPING */}
        {activeTab === 'news' && (
          <NewsView />
        )}
      </main>

      {/* Anomaly Alerts Modal */}
      <AlertsModal
        isOpen={showAlertsModal}
        onClose={() => {
          setShowAlertsModal(false);
          loadAlertsCount();
        }}
      />

      {/* Footer System Status Bar */}
      <footer className="border-t border-slate-800 bg-[#070b13] py-4 text-xs font-mono text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-slate-300 font-bold">FINBLIX PREDICTION AI</span>
            <span className="text-slate-700">|</span>
            <span>MODEL: 60% TA + 40% NEWS SENTIMENT</span>
            <span className="text-slate-700">|</span>
            <span>EOD FORECAST</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1 text-slate-400">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span>MySQL finblix</span>
            </span>
            <span className="flex items-center space-x-1 text-slate-400">
              <Server className="w-3.5 h-3.5 text-emerald-400" />
              <span>FastAPI Port 8000</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
