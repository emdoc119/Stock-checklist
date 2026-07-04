from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
import yfinance as yf
from pydantic import BaseModel
from typing import List, Optional

from database import get_db, engine
from models import Base, User, Portfolio, Security, Position, SecurityEvaluation, TradeJournal

app = FastAPI(title="Farmer OS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MarketData(BaseModel):
    kospi_val: float
    kospi_diff: float
    nasdaq_val: float
    nasdaq_diff: float
    kospi_history: List[float]
    nasdaq_history: List[float]

class PositionBase(BaseModel):
    symbol: str
    quantity: float
    avg_price: float

class EvaluationBase(BaseModel):
    structural_growth_score: int
    bottleneck_score: int
    valuation_score: int
    financial_safety_score: int
    momentum_score: int
    sentiment_score: int
    thesis_text: Optional[str] = None

class JournalBase(BaseModel):
    symbol: str
    side: str
    hypothesis_text: str
    checklist_passed: bool

@app.get("/api/market", response_model=MarketData)
def get_market_data():
    try:
        kospi = yf.Ticker("^KS11")
        ndx = yf.Ticker("^IXIC")
        k_hist = kospi.history(period="1mo")
        n_hist = ndx.history(period="1mo")
        
        k_curr = k_hist['Close'].iloc[-1] if not k_hist.empty else 0
        k_prev = k_hist['Close'].iloc[-2] if len(k_hist) > 1 else 0
        n_curr = n_hist['Close'].iloc[-1] if not n_hist.empty else 0
        n_prev = n_hist['Close'].iloc[-2] if len(n_hist) > 1 else 0
        
        return MarketData(
            kospi_val=k_curr, kospi_diff=k_curr - k_prev,
            nasdaq_val=n_curr, nasdaq_diff=n_curr - n_prev,
            kospi_history=k_hist['Close'].tolist()[-30:] if not k_hist.empty else [],
            nasdaq_history=n_hist['Close'].tolist()[-30:] if not n_hist.empty else []
        )
    except Exception as e:
        return MarketData(kospi_val=0, kospi_diff=0, nasdaq_val=0, nasdaq_diff=0, kospi_history=[], nasdaq_history=[])

@app.get("/api/info/{symbol}")
def get_stock_info(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "marketCap": info.get("marketCap"),
            "forwardPE": info.get("forwardPE") or info.get("trailingPE"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "dividendYield": info.get("dividendYield"),
            "sector": info.get("sector")
        }
    except Exception:
        return {}

@app.get("/api/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
    pos_data = []
    total_val = 0
    for p in positions:
        val = p.quantity * p.avg_price
        total_val += val
        pos_data.append({
            "id": p.id,
            "symbol": p.security.symbol,
            "name": p.security.name,
            "quantity": p.quantity,
            "avg_price": p.avg_price,
            "current_value": val
        })
        
    return {
        "name": portfolio.name,
        "target_cash_pct": portfolio.target_cash_pct,
        "total_value": total_val,
        "positions": pos_data
    }

@app.post("/api/portfolio/position")
def update_position(pos: PositionBase, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).first()
    sec = db.query(Security).filter(Security.symbol == pos.symbol).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Security not found")
        
    db_pos = db.query(Position).filter(Position.portfolio_id == portfolio.id, Position.security_id == sec.id).first()
    if db_pos:
        db_pos.quantity = pos.quantity
        db_pos.avg_price = pos.avg_price
    else:
        db_pos = Position(portfolio_id=portfolio.id, security_id=sec.id, quantity=pos.quantity, avg_price=pos.avg_price)
        db.add(db_pos)
    db.commit()
    return {"message": "Position updated"}

@app.get("/api/securities")
def get_securities(db: Session = Depends(get_db)):
    secs = db.query(Security).all()
    return [{"symbol": s.symbol, "name": s.name} for s in secs]

@app.post("/api/securities")
def add_security(symbol: str, name: str, country: str, db: Session = Depends(get_db)):
    if db.query(Security).filter(Security.symbol == symbol).first():
        raise HTTPException(status_code=400, detail="Security already exists")
    s = Security(symbol=symbol, name=name, country=country)
    db.add(s)
    db.commit()
    return {"message": "Security added"}

@app.get("/api/evaluation/{symbol}")
def get_evaluation(symbol: str, db: Session = Depends(get_db)):
    sec = db.query(Security).filter(Security.symbol == symbol).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Security not found")
    
    ev = db.query(SecurityEvaluation).filter(SecurityEvaluation.security_id == sec.id).first()
    if not ev:
        return {}
    
    return {
        "structural_growth_score": ev.structural_growth_score,
        "bottleneck_score": ev.bottleneck_score,
        "valuation_score": ev.valuation_score,
        "financial_safety_score": ev.financial_safety_score,
        "momentum_score": ev.momentum_score,
        "sentiment_score": ev.sentiment_score,
        "farmer_score": ev.farmer_score,
        "thesis_text": ev.thesis_text
    }

@app.post("/api/evaluation/{symbol}")
def update_evaluation(symbol: str, ev: EvaluationBase, db: Session = Depends(get_db)):
    sec = db.query(Security).filter(Security.symbol == symbol).first()
    if not sec:
        raise HTTPException(status_code=404, detail="Security not found")
        
    db_ev = db.query(SecurityEvaluation).filter(SecurityEvaluation.security_id == sec.id).first()
    if not db_ev:
        db_ev = SecurityEvaluation(security_id=sec.id)
        db.add(db_ev)
        
    db_ev.structural_growth_score = ev.structural_growth_score
    db_ev.bottleneck_score = ev.bottleneck_score
    db_ev.valuation_score = ev.valuation_score
    db_ev.financial_safety_score = ev.financial_safety_score
    db_ev.momentum_score = ev.momentum_score
    db_ev.sentiment_score = ev.sentiment_score
    db_ev.thesis_text = ev.thesis_text
    
    total = (ev.structural_growth_score + ev.bottleneck_score + ev.valuation_score + 
             ev.financial_safety_score + ev.momentum_score + ev.sentiment_score) / 30.0 * 100
    db_ev.farmer_score = total
    db_ev.evaluation_date = date.today()
    
    db.commit()
    return {"message": "Evaluation updated", "farmer_score": total}

@app.get("/api/journals")
def get_journals(db: Session = Depends(get_db)):
    journals = db.query(TradeJournal).order_by(TradeJournal.created_at.desc()).limit(20).all()
    return [{
        "id": j.id,
        "symbol": j.symbol,
        "side": j.side,
        "checklist_passed": j.checklist_passed,
        "hypothesis_text": j.hypothesis_text,
        "created_at": j.created_at.isoformat()
    } for j in journals]

@app.post("/api/journals")
def add_journal(journal: JournalBase, db: Session = Depends(get_db)):
    j = TradeJournal(
        symbol=journal.symbol,
        side=journal.side,
        hypothesis_text=journal.hypothesis_text,
        checklist_passed=journal.checklist_passed
    )
    db.add(j)
    db.commit()
    return {"message": "Journal added"}
