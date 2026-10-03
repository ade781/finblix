import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getTickers = (category = null) => {
  const params = category && category !== 'all' ? { category } : {};
  return api.get('/market/tickers', { params });
};

export const getMarketHistory = (symbol, timeframe = '1d', limit = 150) => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.get(`/market/history/${encodedSymbol}`, {
    params: { timeframe, limit },
  });
};

export const getIndicators = (symbol, timeframe = '1d') => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.get(`/indicators/${encodedSymbol}`, {
    params: { timeframe },
  });
};

export const getScreenerOverview = (category = null, sortBy = 'gainers') => {
  return api.get('/screener/overview', {
    params: { category, sort_by: sortBy },
  });
};

export const simulateWhatIf = (payload) => {
  return api.post('/simulation/what-if', payload);
};

export const calculateRisk = (payload) => {
  return api.post('/simulation/risk-calculator', payload);
};

export const getNewsFeed = (limit = 10) => {
  return api.get('/news/feed', { params: { limit } });
};

export const getFearGreed = () => {
  return api.get('/news/fear-greed');
};

// --- Backtest API ---
export const runBacktest = (payload) => {
  return api.post('/backtest/run', payload);
};

// --- Paper Trading Portfolio API ---
export const getPortfolioSummary = () => {
  return api.get('/portfolio/summary');
};

export const buyAsset = (payload) => {
  return api.post('/portfolio/buy', payload);
};

export const closeTrade = (tradeId) => {
  return api.post(`/portfolio/close/${tradeId}`);
};

export const resetPortfolio = () => {
  return api.post('/portfolio/reset');
};

// --- Anomaly Alerts API ---
export const getAlerts = (unreadOnly = false) => {
  return api.get('/alerts/', { params: { unread_only: unreadOnly } });
};

export const scanAnomalies = () => {
  return api.post('/alerts/scan');
};

export const markAlertRead = (alertId) => {
  return api.post(`/alerts/mark-read/${alertId}`);
};

// --- Daily Direction Prediction API ---
export const getDailyPrediction = (symbol) => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.get(`/prediction/daily/${encodedSymbol}`);
};



export const trainModel = (symbol, rf = 300, gb = 250) => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.post(`/prediction/train/${encodedSymbol}?n_estimators_rf=${rf}&n_estimators_gb=${gb}`);
};

export const getModelStatus = (symbol) => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.get(`/prediction/model-status/${encodedSymbol}`);
};

// --- Prediksi 3 Jam ke Depan (Training 7 Hari + Scraping Massal Harian) ---
export const getThreeHourPrediction = (symbol) => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.get(`/prediction/three-hours/${encodedSymbol}`);
};

export const trainThreeHourModel = (symbol) => {
  const encodedSymbol = encodeURIComponent(symbol);
  return api.post(`/prediction/train-three-hours/${encodedSymbol}`);
};

export const triggerBulkScrapeNews = (limitPerFeed = 25) => {
  return api.post(`/prediction/scrape-daily-news?limit_per_feed=${limitPerFeed}`);
};

export default api;

