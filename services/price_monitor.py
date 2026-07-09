import time
import yfinance as yf
from sqlalchemy.orm import Session
from database import SessionLocal
from models import WatchlistItem, AlertLog
from services.telegram_bot import send_alert, format_alert_message

def check_prices():
    db: Session = SessionLocal()
    try:
        items = db.query(WatchlistItem).filter(WatchlistItem.is_active == True).all()
        for item in items:
            try:
                hist = yf.Ticker(item.symbol).history(period="5d")
                if len(hist) < 2:
                    continue
                
                prev_close = float(hist['Close'].iloc[-2])
                current_price = float(hist['Close'].iloc[-1])
                change_pct = ((current_price - prev_close) / prev_close) * 100
                
                if abs(change_pct) >= item.alert_threshold_pct:
                    alert_type = f"SURGE_{item.alert_threshold_pct}" if change_pct > 0 else f"DROP_{item.alert_threshold_pct}"
                    
                    # Check if already alerted today
                    # For simplicity, just checking the last 24h could be added here.
                    
                    msg = format_alert_message(item.symbol, change_pct, current_price, item.alert_threshold_pct)
                    sent = send_alert(msg)
                    
                    if sent:
                        log = AlertLog(
                            symbol=item.symbol,
                            alert_type=alert_type,
                            price_at_alert=current_price,
                            change_pct=change_pct,
                            sent_via="TELEGRAM"
                        )
                        db.add(log)
                        db.commit()
            except Exception as e:
                print(f"Error checking {item.symbol}: {e}")
    finally:
        db.close()

def start_monitor_daemon():
    # This should be run in a separate background thread or process
    while True:
        check_prices()
        time.sleep(3600)  # Check every hour
