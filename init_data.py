from database import engine, SessionLocal
from models import Base, User, Portfolio, Security, TossApiConfig, TradeOrder

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if user exists
    user = db.query(User).filter(User.name == "Farmer").first()
    if not user:
        user = User(name="Farmer")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Add Portfolio
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(user_id=user.id, name="Core Portfolio", target_cash_pct=0.1)
        db.add(portfolio)
        db.commit()
        
    # Add some securities (KR & US)
    securities = [
        {"symbol": "005930.KS", "name": "Samsung Electronics", "country": "KR"},
        {"symbol": "NVDA", "name": "NVIDIA", "country": "US"},
        {"symbol": "AAPL", "name": "Apple", "country": "US"}
    ]
    
    for sec in securities:
        s = db.query(Security).filter(Security.symbol == sec["symbol"]).first()
        if not s:
            s = Security(**sec)
            db.add(s)
    
    db.commit()
    db.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
