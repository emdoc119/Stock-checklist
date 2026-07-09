import os

def get_toss_access_token():
    api_key = os.getenv("TOSS_API_KEY")
    secret_key = os.getenv("TOSS_SECRET_KEY")
    
    if not api_key or not secret_key:
        return None
        
    # Toss Open API mock
    return "MOCK_TOSS_TOKEN"

def get_toss_portfolio(token):
    # Mock implementation
    if not token:
        return []
    
    return [
        {"symbol": "AAPL", "quantity": 10, "avg_price": 160.0},
        {"symbol": "NVDA", "quantity": 5, "avg_price": 110.0}
    ]
