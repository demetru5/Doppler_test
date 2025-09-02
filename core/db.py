import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Enum, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import get_config
from datetime import datetime

config = get_config()

# MySQL connection string
MYSQL_USER = getattr(config, 'MYSQL_USER', 'root')
MYSQL_PASSWORD = getattr(config, 'MYSQL_PASSWORD', '')
MYSQL_HOST = getattr(config, 'MYSQL_HOST', 'localhost')
MYSQL_DB = getattr(config, 'MYSQL_DB', 'doppler-db')

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(100))
    lastName = Column(String(100))
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    isAdmin = Column(Boolean, default=False)
    isActive = Column(Boolean, default=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    lastLogin = Column(DateTime)
    # Add other fields as needed

    moomoo_accounts = relationship('MoomooAccount', back_populates='user')

# MoomooAccount model
class MoomooAccount(Base):
    __tablename__ = 'moomoo_accounts'
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey('users.id'))
    accountId = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    password = Column(String(255))
    tradingPassword = Column(String(255))
    host = Column(String(255))
    port = Column(Integer)
    status = Column(String(50), default='pending')
    tradingEnabled = Column(Boolean, default=False)
    tradingAmount = Column(Float, default=10.0)
    createdAt = Column(DateTime, default=datetime.utcnow)
    updatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approvedAt = Column(DateTime)
    approvedBy = Column(Integer)
    rejectedAt = Column(DateTime)
    rejectedBy = Column(Integer)
    rejectionReason = Column(String(255))
    cashAccountId = Column(BigInteger)
    marginAccountId = Column(BigInteger)
    tradingAccount = Column(Enum('cash', 'margin', name='trading_account_type', default='cash'))

    user = relationship('User', back_populates='moomoo_accounts')

# StrategyHistory model
class StrategyHistory(Base):
    __tablename__ = 'strategy_history'
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    strategy_name = Column(String(255), nullable=False)
    entry_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    stop_price = Column(Float, nullable=False)
    lock_time = Column(DateTime)
    buy_time = Column(DateTime)
    hold_time = Column(DateTime)
    probability = Column(Float, default=0.0)
    match_score = Column(Float, default=0.0)
    pattern_type = Column(String(100))
    description = Column(String(500))
    completion_type = Column(String(50), nullable=False)  # 'sell', 'stop', 'target'
    completion_time = Column(DateTime, nullable=False)
    final_price = Column(Float)  # Price when strategy was completed
    profit_loss = Column(Float)  # Calculated P&L
    profit_loss_percent = Column(Float)  # P&L as percentage
    target_history = Column(String(1000))  # JSON string of target history
    VWAP = Column(Float)
    RSI = Column(Float)
    StochRSI_K = Column(Float)
    StochRSI_D = Column(Float)
    MACD = Column(Float)
    MACD_signal = Column(Float)
    MACD_hist = Column(Float)
    ADX = Column(Float)
    DMP = Column(Float)
    DMN = Column(Float)
    Supertrend = Column(Float)
    Trend = Column(Float)
    PSAR_L = Column(Float)
    PSAR_S = Column(Float)
    PSAR_R = Column(Float)
    EMA200 = Column(Float)
    EMA21 = Column(Float)
    EMA9 = Column(Float)
    EMA4 = Column(Float)
    EMA5 = Column(Float)
    VWAP_Slope = Column(Float)
    Volume_Ratio = Column(Float)
    ROC = Column(Float)
    Williams_R = Column(Float)
    ATR = Column(Float)
    HOD = Column(Float)
    ATR_to_HOD = Column(Float)
    ATR_to_VWAP = Column(Float)
    ZenP = Column(Float)
    RVol = Column(Float)
    BB_lower = Column(Float)
    BB_mid = Column(Float)
    BB_upper = Column(Float)
    ATR_Spread = Column(Float)
    session = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Dependency for getting DB session
# Usage: with get_db() as db: ...
from contextlib import contextmanager
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# To create tables in the database (run once)
def init_db():
    Base.metadata.create_all(bind=engine) 