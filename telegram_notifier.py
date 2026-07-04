import os
import requests
import logging

logger = logging.getLogger(__name__)

def send_telegram_message(message: str):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not bot_token or not chat_id:
        logger.info(f"[Telegram Mock] Message: {message}")
        print(f"[Telegram Mock] Message: {message}")
        return
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        print(f"Failed to send Telegram message: {e}")
