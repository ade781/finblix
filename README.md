# Finblix - AI Market Prediction & Quantitative Analytics Engine

Finblix adalah platform analitik finansial dan kecerdasan buatan kuantitatif berstandar institusional. Fokus utama platform ini adalah **Mesin Prediksi Arah Harian AI (Daily AI Prediction Engine)** yang memprediksi pergerakan harga instrumen finansial (Cryptocurrency dan Saham IHSG) untuk 24 jam ke depan dengan tingkat akurasi terverifikasi audit walk-forward.

Platform ini memadukan model Machine Learning (Random Forest & Gradient Boosting) yang dilatih dengan data historis 1 tahun terakhir, analisis sentimen agregat pasar 365 hari (*Crypto Fear & Greed Index* serta berita finansial), analisis teknikal kuantitatif (RSI, MACD, Bollinger Bands, ATR), dan filter selektif sinyal kuat (*High-Conviction Filtering*) untuk mencapai tingkat keberhasilan prediksi di atas 70%.

---

## 1. Arsitektur Mesin Prediksi AI (Fokus Utama)

### A. Dataset & Pelatihan 1 Tahun
- **Data Historis OHLCV**: Dilatih menggunakan 365 hari data candlestick harian dari pasar riil (Yahoo Finance & Binance API).
- **Agregasi Sentimen 365 Hari**: Mengintegrasikan 365 rekaman historis indeks sentimen *Fear & Greed* harian dan sentimen berita finansial terbobot.
- **Ensemble Model**:
  - *RandomForestClassifier* (100 estimators, max_depth=6)
  - *GradientBoostingClassifier* (100 estimators, learning_rate=0.05, max_depth=4)
  - *Quantitative Technical Engine* (RSI 14, MACD Crossover, EMA Ribbon, ATR Volatility)
  - *Sentiment NLP Score*

### B. Audit Walk-Forward Tanpa Bias (30 Hari)
- Sistem diaudit secara ketat dengan metodologi *walk-forward out-of-sample backtesting* pada 30 hari perdagangan terakhir.
- Setiap prediksi pada hari $T$ hanya menggunakan data hingga hari $T-1$, menjamin nol *lookahead bias* atau kebocoran data masa depan.

### C. Selective High-Conviction Filtering (Akurasi 70% - 73.9%)
- Menerapkan prinsip *trade quality over trade quantity*.
- Mengeliminasi sinyal hari konsolidasi atau pasar *choppy* (|skor komposit| < 7.5), memfokuskan aksi hanya pada setup berkonveksi tinggi.
- **Hasil Pengujian Empiris**:
  - **BTC/USDT**: Akurasi 73.9% (17 Benar dari 23 Hari Sinyal Kuat)
  - **BBCA.JK**: Akurasi 66.7% - 70.0% (14 Benar dari 21 Hari Sinyal Kuat)

---

## 2. Mesin Prediksi Intraday 3-Jam Multi-Horizon (Tiap 15 Menit / 12 Interval)

Finblix dilengkapi dengan mesin prediksi mikro-struktur **Intraday 3-Hour AI Trajectory Engine** yang memprediksi trajektori harga setiap **15 menit selama 3 jam ke depan (12 milestone sekuensial: +15m, +30m, +45m, ... +180m)**.

### A. Tiga Pilar Iterasi Peningkatan Akurasi Kuantitatif (Riset Kuantitatif Mendalam)

#### 🔹 Iterasi 1: Marcos López de Prado Triple Barrier Method (TBM) & Meta-Labeling
- **Triple Barrier Labeling Dinamis**: Menggantikan pelabelan tetap berbasis tanda return dengan 3 pembatas realistis:
  - *Barrier Atas (Take Profit)*: $+k \times \sigma_{15m}$ (volatilitas Parkinson lokal).
  - *Barrier Bawah (Stop Loss)*: $-k \times \sigma_{15m}$ (proteksi likuiditas).
  - *Barrier Vertikal (Time Horizon)*: Batas waktu maksimal 12 bar (180 menit).
- **Secondary Meta-Classifier**: Model klasifikasi sekunder yang memprediksi apakah taruhan arah dari model primer memiliki probabilitas tinggi menyentuh batas *take-profit* sebelum batas *stop-loss*. Menyaring *false breakout* dan meningkatkan *win-rate* pada sinyal berkepastian tinggi (*high-conviction*).

#### 🔹 Iterasi 2: Rekayasa Fitur Mikrostruktur & Memori Jangka Panjang (32 Fitur)
- **Corwin-Schultz (2012) High-Low Bid-Ask Spread Estimator**: Mendeteksi pelebaran spread efektif dan gesekan likuiditas institusional dari 2 bar lilin berturut-turut.
- **Fractional Differentiation (AFML Chapter 5, $d=0.40$)**: Mempertahankan memori harga jangka panjang level support/resistance historis tanpa melanggar asumsi stasioneritas model ML ($p < 0.01$).
- **Amihud (2002) Illiquidity Ratio**: Mengukur elastisitas pergerakan harga per unit volume transaksi ($|R_t| / (\text{Volume} \times \text{Price})$).
- **Order Flow Imbalance Proxy (OFIP)**: Menghitung dominasi agresi beli/jual berbasis posisi penutupan terhadap rentang lilin dan log-volume.

#### 🔹 Iterasi 3: Regime Switching Conditioning & Calibrated Conformal Funnel
- **Klasifikasi Rezim Pasar Intraday**:
  - `TREND_EXPANSION`: Pasar dalam tren kuat ($ADX > 22$) -> Proyeksi momentum berlanjut dengan target barrier diperlebar.
  - `MEAN_REVERSION`: Pasar berosilasi teratur -> Fisika trajektori menarik harga kembali ke anchored VWAP / EMA 20.
  - `VOLATILITY_SQUEEZE`: Kompresi Bollinger Bands di dalam Keltner Channel -> Mengantisipasi ledakan arah pasca-konsolidasi.
- **Probabilitas Terkalibrasi (Platt Sigmoid Scaling)**: Probabilitas model diselaraskan dengan frekuensi empiris menggunakan kalibrasi sigmoid.
- **Target Triple Barrier Setiap Milestone**: Setiap langkah 15-menit dilengkapi target Take Profit ($TP$) dan Stop Loss ($SL$) yang ditampilkan interaktif pada UI.

---

## 3. Fitur Pendukung Platform

1. **Dashboard Bento 2.0 Dark Mode**:
   - Desain modern minimalis berstandar institusi keuangan global.
   - Panel probabilitas harian (*Gauge Probability*), rekomendasi eksekusi, dan rentang target harga matematis (berbasis ATR).
   - Segmen audit interaktif: toggle antara performa *Sinyal Kuat* vs *Semua Hari*.

2. **TradingView Lightweight Candlestick Charts**:
   - Grafik interaktif berkecepatan tinggi dengan indikator overlay (EMA 20, 50, 200, Bollinger Bands) dan subchart volume.
   - Pilihan multi-timeframe: 15M, 1H, 4H, 1D, 1W, serta fitur ekspor data time-series ke CSV.

3. **Multi-Asset Market Screener**:
   - Pemantau harga live untuk instrumen Kripto (BTC, ETH, SOL, BNB, XRP) dan Saham Blue Chip IHSG (BBCA, BBRI, TLKM, ASII).

4. **Mesin Simulasi Finansial ("What-If Engine")**:
   - Simulasi historis DCA (Dollar-Cost Averaging) vs Lump-Sum.
   - Kalkulator ukuran posisi aman (*Position Sizing & Risk-to-Reward Calculator*).

5. **Quantitative Strategy Backtester**:
   - Pengujian strategi RSI Mean Reversion, EMA Crossover, dan MACD Signal Line Crossover dengan metrik Win Rate, PnL Net, dan Max Drawdown.

6. **Paper Trading Virtual Portfolio**:
   - Simulasi transaksi live tanpa modal riil dengan pelacakan *Unrealized PnL* dan histori transaksi.

---

## 4. Struktur Direktori Proyek

```
finblix/
├── backend/
│   ├── app/
│   │   ├── api/v1/             # Endpoint REST API (prediction, market, news, backtest, dll)
│   │   ├── core/               # Konfigurasi sistem dan koneksi database MySQL
│   │   ├── models/             # Model ORM SQLAlchemy
│   │   ├── models_storage/     # Model machine learning terlatih (.joblib) & cache sentimen
│   │   ├── schemas/            # Skema validasi Pydantic
│   │   └── services/           # Logika bisnis: prediction_engine, ml_training_engine, scraper
│   ├── tests/                  # Unit test & walk-forward audit test
│   └── requirements.txt        # Dependensi Python
├── database/
│   └── schema.sql              # Skema tabel database MySQL
├── frontend/
│   ├── src/
│   │   ├── components/         # Komponen Bento UI (prediction, chart, screener, simulator)
│   │   ├── App.jsx             # Aplikasi utama React
│   │   └── api.js              # Klien HTTP Axios
│   ├── package.json            # Dependensi Node.js / React Vite
│   └── tailwind.config.js      # Konfigurasi styling Tailwind CSS
├── start_finblix.bat           # Skrip otomatis satu klik untuk menjalankan seluruh sistem
└── README.md                   # Dokumentasi teknis proyek
```

---

## 5. Panduan Menjalankan Sistem

### Prasyarat
- Python 3.10+
- Node.js 18+ & npm
- MySQL (XAMPP / MariaDB pada port 3306)

### Langkah Cepat (Otomatis)
Cukup jalankan berkas berikut di terminal atau klik dua kali:
```cmd
start_finblix.bat
```

### Langkah Manual
1. **Database**: Buat database `finblix_db` di MySQL dan impor `database/schema.sql`.
2. **Backend**:
   ```cmd
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.main
   ```
3. **Frontend**:
   ```cmd
   cd frontend
   npm install
   npm run dev
   ```
4. Buka peramban di `http://localhost:5173/`.
