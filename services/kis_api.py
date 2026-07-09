import os
import requests

def get_kis_access_token():
    app_key = os.getenv("KIS_APP_KEY")
    app_secret = os.getenv("KIS_APP_SECRET")
    mode = os.getenv("KIS_MODE", "virtual")
    
    if not app_key or not app_secret:
        return None
        
    base_url = "https://openapi.koreainvestment.com:9443" if mode == "real" else "https://openapivts.koreainvestment.com:29443"
    
    url = f"{base_url}/oauth2/tokenP"
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    try:
        res = requests.post(url, json=body)
        res.raise_for_status()
        return res.json().get("access_token")
    except Exception as e:
        print(f"KIS Token Error: {e}")
        return None

def get_kis_balance(token):
    # This is a mock implementation.
    # In production, use the KIS /uapi/domestic-stock/v1/trading/inquire-balance endpoint.
    account_no = os.getenv("KIS_ACCOUNT_NO")
    if not token or not account_no:
        return []
    
    return [
        {"symbol": "005930.KS", "quantity": 50, "avg_price": 72000},
        {"symbol": "035420.KS", "quantity": 20, "avg_price": 190000}
    ]
