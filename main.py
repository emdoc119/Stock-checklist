from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import date, datetime
import yfinance as yf
from pydantic import BaseModel
from typing import List, Optional

from database import get_db, engine, SessionLocal
from models import Base, User, Portfolio, Security, Position, SecurityEvaluation, TradeJournal, TradeOrder
import pandas as pd
import random
import os
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from telegram_notifier import send_telegram_message
from contextlib import asynccontextmanager

from screener import run_screener

load_dotenv('.env.md')
load_dotenv('.env')  # Overrides with .env if exists

from toss_api_client import TossApiClient

EXECUTE_REAL_TRADES = False

def daily_brief_job():
    print("Running daily_brief_job...")
    try:
        vix_ticker = yf.Ticker("^VIX")
        vix_hist = vix_ticker.history(period="1d")
        vix_value = float(vix_hist['Close'].iloc[-1]) if not vix_hist.empty else 0.0
        
        fear_greed_index = random.uniform(0, 100)
        
        top_picks = run_screener()
        
        msg_lines = [
            "📊 [Daily Market Brief]",
            f"VIX: {vix_value:.2f}",
            f"Fear & Greed (Mock): {fear_greed_index:.1f}",
            "",
            "🎯 [Top Screener Picks]"
        ]
        
        if top_picks:
            for p in top_picks:
                ma_info = f"120MA Dist: {p['ma_120_dist_pct']:.1f}%" if p['ma_120_dist_pct'] is not None else "N/A"
                msg_lines.append(f"- {p['symbol']}: Price={p['price']:.2f}, RSI={p['rsi_14']:.1f}, {ma_info}")
        else:
            msg_lines.append("No picks met the criteria today.")
            
        send_telegram_message("\n".join(msg_lines))
        
    except Exception as e:
        print(f"Error in daily_brief_job: {e}")

def check_indicators_job():
    print("Running check_indicators_job...")
    db = SessionLocal()
    try:
        securities = db.query(Security).all()
        symbols_to_check = set([s.symbol for s in securities])
        
        for symbol in symbols_to_check:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")
                if hist.empty or len(hist) < 2:
                    continue
                
                closes = hist['Close']
                current_price = float(closes.iloc[-1])
                prev_price = float(closes.iloc[-2])
                
                daily_return = (current_price - prev_price) / prev_price
                alerts = []
                
                if daily_return <= -0.05:
                    alerts.append(f"급락 알림: {-daily_return*100:.1f}% 하락 (현재가: {current_price:.2f})")
                
                mas = [5, 20, 60, 120]
                for ma_days in mas:
                    if len(closes) >= ma_days:
                        ma_val = float(closes.tail(ma_days).mean())
                        if abs(current_price - ma_val) / ma_val <= 0.05:
                            alerts.append(f"이평선 접근: {ma_days}일선({ma_val:.2f})의 ±5% 이내")
                
                if len(closes) >= 14:
                    delta = closes.diff()
                    gain = delta.where(delta > 0, 0.0)
                    loss = -delta.where(delta < 0, 0.0)
                    avg_gain = gain.ewm(com=13, min_periods=14).mean()
                    avg_loss = loss.ewm(com=13, min_periods=14).mean()
                    rs = avg_gain / avg_loss
                    rsi_series = 100 - (100 / (1 + rs))
                    rsi_val = float(rsi_series.iloc[-1])
                else:
                    rsi_val = 50.0
                    
                fear_greed_index = random.uniform(0, 100)
                
                if rsi_val < 30 or fear_greed_index < 30:
                    alerts.append(f"매수 적기 (공포): RSI={rsi_val:.1f}, F&G={fear_greed_index:.1f}")
                
                if alerts:
                    msg = "\n".join(alerts)
                    send_telegram_message(f"[{symbol} 지표 알림]\n{msg}")
                    
            except Exception as e:
                print(f"Error in check_indicators_job for {symbol}: {e}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = BackgroundScheduler()
    # Run every 1 hour
    scheduler.add_job(check_indicators_job, 'interval', hours=1)
    
    # Run daily brief at 17:00
    scheduler.add_job(daily_brief_job, 'cron', hour=17, minute=0)
    
    # Also run once on startup for testing
    daily_brief_job()
    
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Farmer OS API", lifespan=lifespan)

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
    kosdaq_val: float
    kosdaq_diff: float
    sp500_val: float
    sp500_diff: float
    russell_val: float
    russell_diff: float
    kospi_history: List[float]
    nasdaq_history: List[float]
    kosdaq_history: List[float]
    sp500_history: List[float]
    russell_history: List[float]

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
        tickers = {
            "kospi": "^KS11",
            "nasdaq": "^IXIC",
            "kosdaq": "^KQ11",
            "sp500": "^GSPC",
            "russell": "^RUT"
        }
        
        results = {}
        for key, symbol in tickers.items():
            val = 0.0
            diff = 0.0
            hist_list = []
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period="1mo")
                if not hist.empty:
                    val = float(hist['Close'].iloc[-1])
                    prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else val
                    diff = val - prev
                    hist_list = hist['Close'].tolist()[-30:]
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
            
            results[key] = {
                "val": val,
                "diff": diff,
                "hist": hist_list
            }

        return MarketData(
            kospi_val=results["kospi"]["val"], kospi_diff=results["kospi"]["diff"],
            nasdaq_val=results["nasdaq"]["val"], nasdaq_diff=results["nasdaq"]["diff"],
            kosdaq_val=results["kosdaq"]["val"], kosdaq_diff=results["kosdaq"]["diff"],
            sp500_val=results["sp500"]["val"], sp500_diff=results["sp500"]["diff"],
            russell_val=results["russell"]["val"], russell_diff=results["russell"]["diff"],
            kospi_history=results["kospi"]["hist"],
            nasdaq_history=results["nasdaq"]["hist"],
            kosdaq_history=results["kosdaq"]["hist"],
            sp500_history=results["sp500"]["hist"],
            russell_history=results["russell"]["hist"]
        )
    except Exception as e:
        print(f"Error in get_market_data: {e}")
        return MarketData(
            kospi_val=0.0, kospi_diff=0.0,
            nasdaq_val=0.0, nasdaq_diff=0.0,
            kosdaq_val=0.0, kosdaq_diff=0.0,
            sp500_val=0.0, sp500_diff=0.0,
            russell_val=0.0, russell_diff=0.0,
            kospi_history=[], nasdaq_history=[], kosdaq_history=[], sp500_history=[], russell_history=[]
        )

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
    except Exception as e:
        print(f"Error in get_stock_info for {symbol}: {e}")
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

@app.post("/api/portfolio/init_paper_trading")
def init_paper_trading(db: Session = Depends(get_db)):
    try:
        portfolio = db.query(Portfolio).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
            
        # Set starting cash balance
        portfolio.target_cash_pct = 100000.0
        
        # Clear existing positions
        db.query(Position).filter(Position.portfolio_id == portfolio.id).delete()
        
        db.commit()
        return {"message": "Paper trading initialized with $100,000 cash balance."}
    except Exception as e:
        db.rollback()
        print(f"Error initializing paper trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PaperTradeRequest(BaseModel):
    symbol: str
    quantity: float
    price: float
    side: str

@app.post("/api/portfolio/paper_trade")
def paper_trade(trade: PaperTradeRequest, db: Session = Depends(get_db)):
    try:
        portfolio = db.query(Portfolio).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        sec = db.query(Security).filter(Security.symbol == trade.symbol).first()
        if not sec:
            sec = Security(symbol=trade.symbol, name=trade.symbol, country="US" if not trade.symbol.endswith(".KS") and not trade.symbol.endswith(".KQ") else "KR")
            db.add(sec)
            db.commit()
            db.refresh(sec)
            
        db_pos = db.query(Position).filter(Position.portfolio_id == portfolio.id, Position.security_id == sec.id).first()
        trade_amount = trade.quantity * trade.price
        
        if trade.side.lower() == "buy":
            if portfolio.target_cash_pct is None:
                portfolio.target_cash_pct = 100000.0
            
            if portfolio.target_cash_pct < trade_amount:
                raise HTTPException(status_code=400, detail="Not enough cash")
                
            portfolio.target_cash_pct -= trade_amount
            
            if db_pos:
                total_cost = (db_pos.quantity * db_pos.avg_price) + trade_amount
                db_pos.quantity += trade.quantity
                db_pos.avg_price = total_cost / db_pos.quantity
            else:
                db_pos = Position(portfolio_id=portfolio.id, security_id=sec.id, quantity=trade.quantity, avg_price=trade.price)
                db.add(db_pos)
                
        elif trade.side.lower() == "sell":
            if not db_pos or db_pos.quantity < trade.quantity:
                raise HTTPException(status_code=400, detail="Not enough quantity to sell")
                
            if portfolio.target_cash_pct is None:
                portfolio.target_cash_pct = 0.0
            portfolio.target_cash_pct += trade_amount
            db_pos.quantity -= trade.quantity
            
            if db_pos.quantity == 0:
                db.delete(db_pos)
                
        else:
            raise HTTPException(status_code=400, detail="Invalid side. Use 'buy' or 'sell'.")
            
        db.commit()
        return {"message": f"Successfully paper traded: {trade.side} {trade.quantity} of {trade.symbol}"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/indicators/{symbol}")
def get_indicators(symbol: str):
    try:
        # VIX
        vix_ticker = yf.Ticker("^VIX")
        vix_hist = vix_ticker.history(period="1d")
        vix_value = float(vix_hist['Close'].iloc[-1]) if not vix_hist.empty else 0.0

        # RSI
        symbol_ticker = yf.Ticker(symbol)
        hist = symbol_ticker.history(period="6mo")
        rsi_value = 50.0
        if not hist.empty and len(hist) >= 14:
            close_prices = hist['Close']
            delta = close_prices.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.ewm(com=13, min_periods=14).mean()
            avg_loss = loss.ewm(com=13, min_periods=14).mean()
            rs = avg_gain / avg_loss
            rsi_series = 100 - (100 / (1 + rs))
            rsi_value = float(rsi_series.iloc[-1])

        # Fear & Greed (Mock)
        fear_greed_index = random.uniform(0, 100)

        return {
            "symbol": symbol,
            "vix": float(vix_value),
            "rsi_14": rsi_value,
            "fear_and_greed": fear_greed_index
        }
    except Exception as e:
        print(f"Error in get_indicators for {symbol}: {e}")
        return {
            "symbol": symbol,
            "vix": 0.0,
            "rsi_14": 50.0,
            "fear_and_greed": 50.0
        }

@app.get("/api/screener")
def get_screener():
    try:
        results = run_screener()
        return {"data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class BacktestRequest(BaseModel):
    symbol: str
    strategy: str
    period: str = "5y"

@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    try:
        ticker = yf.Ticker(req.symbol)
        hist = ticker.history(period=req.period)
        if hist.empty:
            raise HTTPException(status_code=400, detail="No historical data found")
            
        closes = hist['Close']
        buy_hold_return = (closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0] * 100
        
        # Buy & Hold MDD
        roll_max = closes.cummax()
        drawdown = closes / roll_max - 1.0
        buy_hold_mdd = drawdown.min() * 100
        
        if req.strategy == "rsi_30_70":
            delta = closes.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.ewm(com=13, min_periods=14).mean()
            avg_loss = loss.ewm(com=13, min_periods=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            in_position = False
            entry_price = 0.0
            cum_return = 1.0
            equity_curve = [1.0] * 14
            
            for i in range(14, len(closes)):
                r = rsi.iloc[i-1]
                price = closes.iloc[i]
                
                if not in_position and r < 30:
                    in_position = True
                    entry_price = price
                elif in_position and r > 70:
                    in_position = False
                    trade_ret = (price - entry_price) / entry_price
                    cum_return *= (1 + trade_ret)
                    
                # Mark to market for equity curve
                if in_position:
                    current_trade_ret = (price - entry_price) / entry_price
                    equity_curve.append(cum_return * (1 + current_trade_ret))
                else:
                    equity_curve.append(cum_return)
            
            strategy_return = (cum_return - 1) * 100
            
            # Strategy MDD
            eq_series = pd.Series(equity_curve)
            eq_roll_max = eq_series.cummax()
            eq_drawdown = eq_series / eq_roll_max - 1.0
            strategy_mdd = eq_drawdown.min() * 100
            
            return {
                "symbol": req.symbol,
                "strategy": req.strategy,
                "period": req.period,
                "buy_hold_return_pct": buy_hold_return,
                "buy_hold_mdd_pct": buy_hold_mdd,
                "strategy_return_pct": strategy_return,
                "strategy_mdd_pct": strategy_mdd
            }
        else:
            raise HTTPException(status_code=400, detail="Unknown strategy")
            
    except Exception as e:
        print(f"Error in backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class OrderBase(BaseModel):
    symbol: str
    side: str
    quantity: float

@app.post("/api/toss/order")
def mock_toss_order(order: OrderBase, db: Session = Depends(get_db)):
    try:
        new_order = TradeOrder(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        client = TossApiClient()
        price = 0.0  # Market order mock
        
        if EXECUTE_REAL_TRADES:
            response_data = client.place_order(
                symbol=order.symbol, 
                qty=order.quantity, 
                side=order.side, 
                price=price
            )
            message = "Order successfully placed via Toss OpenAPI"
            api_payload = response_data
        else:
            message = "Order successfully logged (mock, execution disabled)"
            api_payload = {
                "symbol": order.symbol,
                "quantity": order.quantity,
                "side": order.side,
                "price": price,
                "mocked_endpoint": f"{client.BASE_URL}/trading/orders",
                "simulated": True
            }
            # Attempt to fetch token to verify integration logic
            try:
                token = client.get_access_token()
                api_payload["token_fetched"] = "success" if token else "failed"
            except Exception as e:
                api_payload["token_fetched"] = f"error: {str(e)}"

        return {
            "message": message,
            "order_id": new_order.id,
            "symbol": new_order.symbol,
            "side": new_order.side,
            "quantity": new_order.quantity,
            "api_payload": api_payload
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

