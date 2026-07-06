import streamlit as st
st.set_page_config(page_title="Dashboard", layout="wide")

import yfinance as yf
import requests
import pandas as pd
from database import get_db
from models import Portfolio, Position

st.title("📊 HTS Command Center")

# Fetch market data (5 indices)
@st.cache_data(ttl=3600)
def get_market_data():
    tickers = {
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "NASDAQ": "^IXIC",
        "S&P 500": "^GSPC",
        "Russell 2000": "^RUT"
    }
    
    market_data = {}
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="30d")
            if hist.empty:
                market_data[name] = {"current": 0, "diff": 0, "hist": pd.DataFrame()}
                continue
                
            current = float(hist['Close'].iloc[-1])
            prev = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current
            diff = current - prev
            pct_change = (diff / prev * 100) if prev > 0 else 0
            
            market_data[name] = {
                "current": current,
                "diff": diff,
                "pct_change": pct_change,
                "hist": hist[['Close']]
            }
        except Exception:
            market_data[name] = {"current": 0, "diff": 0, "pct_change": 0, "hist": pd.DataFrame()}
            
    return market_data

@st.cache_data(ttl=60)
def get_indicators(symbol="SPY"):
    try:
        resp = requests.get(f"http://localhost:8000/api/indicators/{symbol}")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"vix": 0.0, "rsi_14": 0.0, "fear_and_greed": 50.0}

with st.spinner('데이터를 불러오는 중입니다...'):
    market_data = get_market_data()
    indicators = get_indicators("SPY")

st.subheader("Global Indices (30-day)")
cols = st.columns(5)
indices_names = ["KOSPI", "KOSDAQ", "NASDAQ", "S&P 500", "Russell 2000"]

for col, name in zip(cols, indices_names):
    with col:
        data = market_data.get(name, {})
        current = data.get("current", 0)
        diff = data.get("diff", 0)
        pct_change = data.get("pct_change", 0)
        hist = data.get("hist", pd.DataFrame())
        
        st.metric(name, f"{current:,.2f}", f"{diff:,.2f} ({pct_change:+.2f}%)")
        if not hist.empty:
            st.line_chart(hist, height=150, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("시장 심리 지표")
    i1, i2 = st.columns(2)
    vix = indicators.get("vix", 0)
    fg = indicators.get("fear_and_greed", 50)
    i1.metric("VIX (변동성 지수)", f"{vix:.2f}", help="VIX가 30 이상이면 시장에 공포가 팽배함을 의미하며, 저가 매수의 기회일 수 있습니다.")
    i2.metric("Fear & Greed Index", f"{fg:.0f}", help="0-25: 극단적 공포, 25-45: 공포, 45-55: 중립, 55-75: 탐욕, 75-100: 극단적 탐욕. 시장 심리를 나타냅니다.")
    
    if vix > 30 or fg < 30:
        st.error("📉 시장 공포 구간 - 씨앗을 뿌릴 준비가 되었는가?")
    elif vix < 15 or fg > 70:
        st.success("📈 시장 낙관 구간 - 수확과 현금 확보를 고려할 때인가?")
    else:
        st.info("➖ 중립 구간 - 인내하며 관찰할 시기")

with col2:
    st.subheader("내 포트폴리오 리스크 상태")
    db = next(get_db())
    portfolio = db.query(Portfolio).first()
    if portfolio:
        positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()
        st.write(f"**포트폴리오명**: {portfolio.name}")
        st.write(f"**보유 종목 수**: {len(positions)}개 (적정: 7개 이하)")
        st.write(f"**목표 현금 비중**: {portfolio.target_cash_pct * 100}%")
        
        if len(positions) >= 7:
            st.warning("⚠️ 종목이 너무 많습니다. 포트폴리오 집중도를 높이세요.")
        else:
            st.success("✅ 포트폴리오 집중도가 양호합니다.")
    else:
        st.write("포트폴리오가 없습니다.")
