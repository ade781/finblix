import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def _create_robust_engine():
    db_url = settings.DATABASE_URL
    if "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    try:
        eng = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False,
            connect_args={"connect_timeout": 2} if "mysql" in db_url else {}
        )
        with eng.connect() as conn:
            pass
        return eng
    except Exception as e:
        logger.warning(f"Database connection to {db_url} failed ({e}). Falling back to SQLite.")
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "finblix.db"))
        sqlite_url = f"sqlite:///{db_path}"
        eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        return eng

engine = _create_robust_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_initialized = False

def init_db():
    global _initialized
    if _initialized:
        return
    try:
        from app.models.asset import Asset
        from app.models.ohlcv import OHLCVBar
        from app.models.news import NewsArticle
        from app.models.indicator import TechnicalSnapshot
        from app.models.simulation import VirtualPortfolio, VirtualTrade
        Base.metadata.create_all(bind=engine)
        
        # Auto-seed default assets if empty or only 1
        db = SessionLocal()
        try:
            if db.query(Asset).count() < 5:
                default_assets = [
                    ('BTC/USDT', 'Bitcoin', 'crypto', 'USD'),
                    ('ETH/USDT', 'Ethereum', 'crypto', 'USD'),
                    ('SOL/USDT', 'Solana', 'crypto', 'USD'),
                    ('BNB/USDT', 'BNB', 'crypto', 'USD'),
                    ('XRP/USDT', 'Ripple', 'crypto', 'USD'),
                    ('DOGE/USDT', 'Dogecoin', 'crypto', 'USD'),
                    ('ADA/USDT', 'Cardano', 'crypto', 'USD'),
                    ('AVAX/USDT', 'Avalanche', 'crypto', 'USD'),
                    ('LINK/USDT', 'Chainlink', 'crypto', 'USD'),
                    ('DOT/USDT', 'Polkadot', 'crypto', 'USD'),
                    ('NEAR/USDT', 'NEAR Protocol', 'crypto', 'USD'),
                    ('SUI/USDT', 'Sui', 'crypto', 'USD'),
                ]
                for sym, name, atype, base in default_assets:
                    if not db.query(Asset).filter(Asset.symbol == sym).first():
                        db.add(Asset(symbol=sym, name=name, asset_type=atype, base_currency=base, is_active=True))
                db.commit()
        except Exception as seed_err:
            logger.warning(f"Error seeding default assets: {seed_err}")
        finally:
            db.close()
            
        _initialized = True
    except Exception as e:
        logger.warning(f"Error auto-creating tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
