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

import os
from dotenv import load_dotenv

load_dotenv()

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

class SecurityBase(BaseModel):
    symbol: str
    name: str
    country: str


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
        try:
            hist = yf.Ticker(p.security.symbol).history(period="1d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
            else:
                current_price = p.avg_price
        except Exception:
            current_price = p.avg_price
            
        val = p.quantity * current_price
        total_val += val
        pos_data.append({
            "id": p.id,
            "symbol": p.security.symbol,
            "name": p.security.name,
            "quantity": p.quantity,
            "avg_price": p.avg_price,
            "current_price": current_price,
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
def add_security(security: SecurityBase, db: Session = Depends(get_db)):
    if db.query(Security).filter(Security.symbol == security.symbol).first():
        raise HTTPException(status_code=400, detail="Security already exists")
    s = Security(symbol=security.symbol, name=security.name, country=security.country)
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

def get_yf_history(symbol, period="1mo"):
    try:
        hist = yf.Ticker(symbol).history(period=period)
        if hist.empty:
            return {"current": 0, "history": []}
        return {
            "current": float(hist['Close'].iloc[-1]),
            "history": [{"date": str(d.date()), "value": float(v)} for d, v in zip(hist.index, hist['Close'])]
        }
    except Exception:
        return {"current": 0, "history": []}

@app.get("/api/macro/indices")
def get_macro_indices():
    return {
        "SP500": get_yf_history("^GSPC"),
        "NASDAQ": get_yf_history("^IXIC"),
        "KOSPI": get_yf_history("^KS11"),
        "KOSDAQ": get_yf_history("^KQ11"),
        "SAMSUNG": get_yf_history("005930.KS")
    }

@app.get("/api/macro/rates")
def get_macro_rates():
    return {
        "DXY": get_yf_history("DX-Y.NYB"),
        "US10Y": get_yf_history("^TNX"),
        "KRW_USD": get_yf_history("KRW=X")
    }

@app.get("/api/macro/commodities")
def get_macro_commodities():
    return {
        "GOLD": get_yf_history("GC=F"),
        "WTI": get_yf_history("CL=F"),
        "BTC": get_yf_history("BTC-USD")
    }

@app.get("/api/macro/vix")
def get_macro_vix():
    return get_yf_history("^VIX")

@app.get("/api/macro/fear-greed")
def get_macro_fear_greed():
    vix = get_yf_history("^VIX")
    v_val = vix.get("current", 20)
    score = max(0, min(100, 100 - (v_val - 10) * 3.5))
    return {"score": int(score)}

from services.kis_api import get_kis_access_token, get_kis_balance
from services.toss_api import get_toss_access_token, get_toss_portfolio

@app.get("/api/broker/sync")
def sync_broker_portfolio(db: Session = Depends(get_db)):
    kis_token = get_kis_access_token()
    toss_token = get_toss_access_token()
    
    positions = []
    if kis_token:
        positions.extend(get_kis_balance(kis_token))
    if toss_token:
        positions.extend(get_toss_portfolio(toss_token))
        
    if not positions:
        return {"message": "No data found or API keys missing."}
        
    portfolio = db.query(Portfolio).first()
    if not portfolio:
        user = db.query(User).first()
        if not user:
            user = User(name="Farmer")
            db.add(user)
            db.commit()
        portfolio = Portfolio(user_id=user.id, name="Default Portfolio")
        db.add(portfolio)
        db.commit()
    
    # Simple sync: add missing securities and update/create positions
    for p in positions:
        sec = db.query(Security).filter(Security.symbol == p['symbol']).first()
        if not sec:
            sec = Security(symbol=p['symbol'], name=p['symbol'], country='KR' if '.KS' in p['symbol'] or '.KQ' in p['symbol'] else 'US')
            db.add(sec)
            db.commit()
            
        pos = db.query(Position).filter(Position.portfolio_id == portfolio.id, Position.security_id == sec.id).first()
        if pos:
            pos.quantity = p['quantity']
            pos.avg_price = p['avg_price']
        else:
            pos = Position(portfolio_id=portfolio.id, security_id=sec.id, quantity=p['quantity'], avg_price=p['avg_price'])
            db.add(pos)
    
    db.commit()
    return {"message": f"Synced {len(positions)} positions from brokers."}

class WatchlistBase(BaseModel):
    symbol: str
    name: str
    alert_threshold_pct: float = 5.0

@app.get("/api/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(WatchlistItem).all()
    return [{"id": i.id, "symbol": i.symbol, "name": i.name, "alert_threshold_pct": i.alert_threshold_pct, "is_active": i.is_active} for i in items]

@app.post("/api/watchlist")
def add_watchlist(item: WatchlistBase, db: Session = Depends(get_db)):
    if db.query(WatchlistItem).filter(WatchlistItem.symbol == item.symbol).first():
        raise HTTPException(status_code=400, detail="Item already in watchlist")
    w = WatchlistItem(symbol=item.symbol, name=item.name, alert_threshold_pct=item.alert_threshold_pct)
    db.add(w)
    db.commit()
    return {"message": "Watchlist added"}

@app.delete("/api/watchlist/{id}")
def delete_watchlist(id: int, db: Session = Depends(get_db)):
    item = db.query(WatchlistItem).filter(WatchlistItem.id == id).first()
    if item:
        db.delete(item)
        db.commit()
    return {"message": "Watchlist deleted"}

@app.get("/api/alerts/history")
def get_alerts_history(db: Session = Depends(get_db)):
    logs = db.query(AlertLog).order_by(AlertLog.created_at.desc()).limit(20).all()
    return [{"id": l.id, "symbol": l.symbol, "alert_type": l.alert_type, "change_pct": l.change_pct, "created_at": l.created_at.isoformat()} for l in logs]

from fastapi import BackgroundTasks
from services.price_monitor import check_prices

@app.post("/api/monitor/start")
def start_monitor(background_tasks: BackgroundTasks):
    background_tasks.add_task(check_prices)
    return {"message": "Monitor task started"}

