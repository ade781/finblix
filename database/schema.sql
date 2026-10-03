-- =============================================================================
-- FINBLIX DATABASE SCHEMA (MySQL / MariaDB via XAMPP)
-- Database Name: finblix
-- Host         : localhost:3306
-- =============================================================================

CREATE DATABASE IF NOT EXISTS finblix
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE finblix;

-- 1. Tabel Master Aset (Kripto, Saham US, Saham IHSG)
CREATE TABLE IF NOT EXISTS assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(30) NOT NULL UNIQUE,       -- Contoh: 'BTC/USDT', 'BBCA.JK', 'AAPL'
    name VARCHAR(100) NOT NULL,               -- Contoh: 'Bitcoin', 'Bank Central Asia', 'Apple Inc'
    asset_type ENUM('crypto', 'stock_idx', 'stock_us', 'forex', 'index') NOT NULL,
    base_currency VARCHAR(10) DEFAULT 'USD',  -- 'USD', 'IDR'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_asset_type (asset_type)
) ENGINE=InnoDB;

-- 2. Tabel Time-Series Candlestick (OHLCV)
CREATE TABLE IF NOT EXISTS ohlcv_bars (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    timeframe VARCHAR(10) NOT NULL,           -- '15m', '1h', '4h', '1d', '1w'
    open_time BIGINT NOT NULL,                -- Unix Epoch Timestamp dalam DETIK (Format TradingView)
    open_time_dt DATETIME NOT NULL,           -- Format tanggal terbaca manusia (UTC)
    open_price DECIMAL(18, 8) NOT NULL,
    high_price DECIMAL(18, 8) NOT NULL,
    low_price DECIMAL(18, 8) NOT NULL,
    close_price DECIMAL(18, 8) NOT NULL,
    volume DECIMAL(24, 8) NOT NULL,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE KEY uq_asset_timeframe_bar (asset_id, timeframe, open_time),
    INDEX idx_fetch_bars (asset_id, timeframe, open_time DESC)
) ENGINE=InnoDB;

-- 3. Tabel Indikator Teknikal Snapshot
CREATE TABLE IF NOT EXISTS technical_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_price DECIMAL(18, 8) NOT NULL,
    change_24h_percent DECIMAL(8, 4),
    rsi_14 DECIMAL(6, 2),
    rsi_status ENUM('oversold', 'neutral', 'overbought') DEFAULT 'neutral',
    macd_line DECIMAL(18, 8),
    macd_signal DECIMAL(18, 8),
    macd_hist DECIMAL(18, 8),
    ema_20 DECIMAL(18, 8),
    ema_50 DECIMAL(18, 8),
    ema_200 DECIMAL(18, 8),
    bollinger_upper DECIMAL(18, 8),
    bollinger_middle DECIMAL(18, 8),
    bollinger_lower DECIMAL(18, 8),
    overall_signal ENUM('strong_buy', 'buy', 'neutral', 'sell', 'strong_sell') DEFAULT 'neutral',
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    INDEX idx_asset_snapshot (asset_id, timeframe)
) ENGINE=InnoDB;

-- 4. Tabel Berita Finansial & Hasil Analisis Sentimen
CREATE TABLE IF NOT EXISTS news_articles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL,             -- 'CNBC Indonesia', 'Kontan', 'CoinDesk'
    article_url VARCHAR(500) NOT NULL UNIQUE,
    published_at DATETIME NOT NULL,
    summary TEXT,
    ai_summary TEXT,                          -- Ringkasan 3 poin AI
    sentiment_score DECIMAL(5, 4) NOT NULL,   -- Rentang -1.0000 s/d +1.0000
    sentiment_label ENUM('bearish', 'neutral', 'bullish') NOT NULL,
    related_symbols VARCHAR(100),             -- 'BTC,ETH' atau 'BBCA.JK'
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_published (published_at DESC),
    INDEX idx_sentiment (sentiment_label)
) ENGINE=InnoDB;

-- 5. Tabel Watchlist Pengguna
CREATE TABLE IF NOT EXISTS user_watchlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) DEFAULT 'default_trader',
    asset_id INT NOT NULL,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_asset (user_name, asset_id)
) ENGINE=InnoDB;

-- 6. Tabel Simulasi Finansial / What-If Portofolio Virtual
CREATE TABLE IF NOT EXISTS virtual_portfolios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_name VARCHAR(50) DEFAULT 'default_trader',
    portfolio_name VARCHAR(100) DEFAULT 'Main Simulation',
    initial_balance DECIMAL(18, 2) DEFAULT 10000.00,
    cash_balance DECIMAL(18, 2) DEFAULT 10000.00,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS virtual_trades (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    portfolio_id INT NOT NULL,
    asset_id INT NOT NULL,
    trade_type ENUM('buy', 'sell') NOT NULL,
    amount DECIMAL(18, 8) NOT NULL,
    entry_price DECIMAL(18, 8) NOT NULL,
    total_cost DECIMAL(18, 2) NOT NULL,
    status ENUM('open', 'closed') DEFAULT 'open',
    closed_price DECIMAL(18, 8) NULL,
    pnl_amount DECIMAL(18, 2) NULL,
    pnl_percent DECIMAL(8, 4) NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (portfolio_id) REFERENCES virtual_portfolios(id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 7. Tabel Log Deteksi Anomali & Sinyal Alert
CREATE TABLE IF NOT EXISTS alert_logs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    asset_id INT NOT NULL,
    alert_type ENUM('volume_spike', 'rsi_oversold', 'rsi_overbought', 'ma_cross', 'price_breakout') NOT NULL,
    message TEXT NOT NULL,
    severity ENUM('info', 'warning', 'critical') DEFAULT 'info',
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    INDEX idx_unread_alerts (is_read, triggered_at DESC)
) ENGINE=InnoDB;

-- Seeding Data Master Awal (Initial Seed)
INSERT IGNORE INTO assets (symbol, name, asset_type, base_currency) VALUES
('BTC/USDT', 'Bitcoin', 'crypto', 'USD'),
('ETH/USDT', 'Ethereum', 'crypto', 'USD'),
('SOL/USDT', 'Solana', 'crypto', 'USD'),
('BNB/USDT', 'BNB', 'crypto', 'USD'),
('XRP/USDT', 'Ripple', 'crypto', 'USD'),
('BBCA.JK', 'Bank Central Asia Tbk', 'stock_idx', 'IDR'),
('BBRI.JK', 'Bank Rakyat Indonesia Tbk', 'stock_idx', 'IDR'),
('TLKM.JK', 'Telkom Indonesia Tbk', 'stock_idx', 'IDR'),
('ASII.JK', 'Astra International Tbk', 'stock_idx', 'IDR'),
('^JKSE', 'IHSG (Indeks Harga Saham Gabungan)', 'index', 'IDR'),
('AAPL', 'Apple Inc', 'stock_us', 'USD'),
('NVDA', 'Nvidia Corporation', 'stock_us', 'USD'),
('TSLA', 'Tesla Inc', 'stock_us', 'USD'),
('MSFT', 'Microsoft Corporation', 'stock_us', 'USD'),
('SPY', 'SPDR S&P 500 ETF Trust', 'stock_us', 'USD');
