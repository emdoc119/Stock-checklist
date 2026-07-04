import streamlit as st
import yfinance as yf
import requests
from database import get_db
from models import Portfolio, Position

st.set_page_config(page_title="Dashboard", layout="wide")
st.title("📊 Dashboard")

# Fetch market data (KOSPI and NASDAQ)
@st.cache_data(ttl=3600)
def get_market_data():
    kospi = yf.Ticker("^KS11")
    ndx = yf.Ticker("^IXIC")
    
    k_hist = kospi.history(period="5d")
    n_hist = ndx.history(period="5d")
    
    k_current = k_hist['Close'].iloc[-1] if not k_hist.empty else 0
    k_prev = k_hist['Close'].iloc[-2] if len(k_hist) > 1 else 0
    
    n_current = n_hist['Close'].iloc[-1] if not n_hist.empty else 0
    n_prev = n_hist['Close'].iloc[-2] if len(n_hist) > 1 else 0
    
    return {
        "KOSPI": (k_current, k_current - k_prev),
        "NASDAQ": (n_current, n_current - n_prev)
    }

@st.cache_data(ttl=60)
def get_indicators(symbol="SPY"):
    try:
        resp = requests.get(f"http://localhost:8000/api/indicators/{symbol}")
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return {"vix": 0.0, "rsi_14": 0.0, "fear_and_greed": 50.0}

market_data = get_market_data()
indicators = get_indicators("SPY")

col1, col2 = st.columns(2)
with col1:
    st.subheader("오늘 시장 사이클 요약")
    m1, m2 = st.columns(2)
    k_val, k_diff = market_data["KOSPI"]
    n_val, n_diff = market_data["NASDAQ"]
    m1.metric("KOSPI", f"{k_val:.2f}", f"{k_diff:.2f}")
    m2.metric("NASDAQ", f"{n_val:.2f}", f"{n_diff:.2f}")
    
    st.subheader("시장 심리 지표")
    i1, i2 = st.columns(2)
    vix = indicators.get("vix", 0)
    fg = indicators.get("fear_and_greed", 50)
    i1.metric("VIX (변동성 지수)", f"{vix:.2f}")
    i2.metric("Fear & Greed Index", f"{fg:.0f}")
    
    # Simple heuristic for UI demo
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
