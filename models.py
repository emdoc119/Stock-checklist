from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from database import engine

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    portfolios = relationship("Portfolio", back_populates="user")

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    target_cash_pct = Column(Float, default=0.1)
    
    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio")

class Security(Base):
    __tablename__ = "securities"
    id = Column(Integer, primary_key=True)
    symbol = Column(String, index=True, unique=True)
    name = Column(String)
    country = Column(String) # 'US', 'KR'
    
    positions = relationship("Position", back_populates="security")
    evaluations = relationship("SecurityEvaluation", back_populates="security")

class Position(Base):
    __tablename__ = "positions"
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"))
    security_id = Column(Integer, ForeignKey("securities.id"))
    quantity = Column(Float, default=0.0)
    avg_price = Column(Float, default=0.0)
    
    portfolio = relationship("Portfolio", back_populates="positions")
    security = relationship("Security", back_populates="positions")

class SecurityEvaluation(Base):
    __tablename__ = "security_evaluations"
    id = Column(Integer, primary_key=True)
    security_id = Column(Integer, ForeignKey("securities.id"))
    evaluation_date = Column(Date)
    
    structural_growth_score = Column(Integer, default=3)
    bottleneck_score = Column(Integer, default=3)
    valuation_score = Column(Integer, default=3)
    financial_safety_score = Column(Integer, default=3)
    momentum_score = Column(Integer, default=3)
    sentiment_score = Column(Integer, default=3)
    
    farmer_score = Column(Float, default=0.0)
    thesis_text = Column(String)
    
    security = relationship("Security", back_populates="evaluations")

class TradeJournal(Base):
    __tablename__ = "trade_journals"
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    side = Column(String) # BUY / SELL
    hypothesis_text = Column(String)
    checklist_passed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
