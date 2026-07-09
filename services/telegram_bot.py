import os
import requests

def send_alert(message: str) -> bool:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram missing keys")
        return False
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return True
    except Exception as e:
        print(f"Telegram Alert Error: {e}")
        return False

def format_alert_message(symbol: str, change_pct: float, current_price: float, threshold: float) -> str:
    is_surge = change_pct >= 0
    icon = "🚀" if is_surge else "🚨"
    action = "급등" if is_surge else "급락"
    
    return f"""{icon} <b>{symbol} {action} 알림</b> {icon}
    
현재가: {current_price:,.2f}
변동률: {change_pct:+.2f}% (목표 ±{threshold}%)

신속하게 대응하세요!"""
