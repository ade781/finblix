import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def _create_robust_engine():
    db_url = settings.DATABASE_URL
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
        _initialized = True
    except Exception as e:
        logger.warning(f"Error auto-creating tables: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
