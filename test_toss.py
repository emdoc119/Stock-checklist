import os
import requests
from dotenv import load_dotenv

load_dotenv('.env.md')
load_dotenv('.env')

app_key = os.getenv("TOSS_API_KEY")
app_secret = os.getenv("TOSS_SECRET_KEY")

print(f"Key loaded: {bool(app_key)}, Secret loaded: {bool(app_secret)}")

if app_key and app_secret:
    # 1. Get Token
    url = "https://openapi.tossinvest.com/v1/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        print(f"Token Status Code: {res.status_code}")
        print(f"Token Response: {res.text}")
        
        if res.status_code == 200:
            token = res.json().get("access_token")
            # 2. Try Balance Endpoint
            balance_url = "https://openapi.tossinvest.com/v1/trading/balances"
            headers = {"Authorization": f"Bearer {token}"}
            bal_res = requests.get(balance_url, headers=headers)
            print(f"Balance Status Code: {bal_res.status_code}")
            print(f"Balance Response: {bal_res.text}")
    except Exception as e:
        print(f"Error: {e}")
