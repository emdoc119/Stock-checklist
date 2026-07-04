import yfinance as yf
import pandas as pd
from typing import List, Dict, Any

def run_screener(symbols: List[str] = None) -> List[Dict[str, Any]]:
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'SPY', 'QQQ']
    
    results = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo")
            if hist.empty or len(hist) < 14:
                continue
                
            closes = hist['Close']
            current_price = float(closes.iloc[-1])
            
            # Calculate 120-day MA
            ma_120 = None
            ma_dist = None
            if len(closes) >= 120:
                ma_120 = float(closes.tail(120).mean())
                ma_dist = abs(current_price - ma_120) / ma_120
            
            # Calculate 14-day RSI
            delta = closes.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.ewm(com=13, min_periods=14).mean()
            avg_loss = loss.ewm(com=13, min_periods=14).mean()
            rs = avg_gain / avg_loss
            rsi_series = 100 - (100 / (1 + rs))
            rsi_val = float(rsi_series.iloc[-1])
            
            # Condition: RSI < 30 OR within 5% of 120-day MA
            ma_condition = (ma_dist is not None and ma_dist <= 0.05)
            
            if rsi_val < 30 or ma_condition:
                results.append({
                    "symbol": symbol,
                    "price": current_price,
                    "rsi_14": rsi_val,
                    "ma_120": ma_120,
                    "ma_120_dist_pct": ma_dist * 100 if ma_dist is not None else None
                })
                
        except Exception as e:
            print(f"Error screening {symbol}: {e}")
            
    return results
