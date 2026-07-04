import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from database import get_db
from models import Portfolio, Position, Security

st.set_page_config(page_title="Portfolio", layout="wide")
st.title("💼 포트폴리오 (집중도 및 리스크 관리)")

db = next(get_db())
portfolio = db.query(Portfolio).first()

if not portfolio:
    st.error("포트폴리오가 존재하지 않습니다.")
    st.stop()

st.subheader(f"포트폴리오: {portfolio.name}")

# Add Position Form
with st.expander("➕ 새로운 포지션 추가 (또는 수정)"):
    securities = db.query(Security).all()
    symbols = [s.symbol for s in securities]
    
    with st.form("add_position_form"):
        sel_symbol = st.selectbox("종목", symbols)
        qty = st.number_input("보유 수량", min_value=0.0, step=1.0)
        avg_price = st.number_input("평균 단가", min_value=0.0, step=1.0)
        submitted = st.form_submit_button("저장")
        
        if submitted:
            sec = db.query(Security).filter(Security.symbol == sel_symbol).first()
            pos = db.query(Position).filter(Position.portfolio_id == portfolio.id, Position.security_id == sec.id).first()
            if pos:
                pos.quantity = qty
                pos.avg_price = avg_price
            else:
                pos = Position(portfolio_id=portfolio.id, security_id=sec.id, quantity=qty, avg_price=avg_price)
                db.add(pos)
            db.commit()
            st.success("포지션 업데이트 완료!")
            st.rerun()

positions = db.query(Position).filter(Position.portfolio_id == portfolio.id).all()

if positions:
    data = []
    total_value = 0
    for p in positions:
        # In a real app, we'd fetch live price here. Using avg_price as current for simplicity in MVP.
        val = p.quantity * p.avg_price
        total_value += val
        data.append({
            "종목": p.security.symbol,
            "수량": p.quantity,
            "평단가": p.avg_price,
            "평가액": val
        })
        
    df = pd.DataFrame(data)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("### 보유 종목 목록")
        st.dataframe(df, use_container_width=True)
    
    with col2:
        st.write("### 비중 분석 (Concentration)")
        if total_value > 0:
            fig = px.pie(df, values='평가액', names='종목', hole=0.3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("보유 금액이 0입니다.")
else:
    st.info("현재 보유 중인 종목이 없습니다.")

st.divider()
st.subheader("🤖 자동매매 (주식 모으기)")
auto_trading_toggle = st.toggle("Auto-Trading (Toss API) - Coming Soon")

if auto_trading_toggle:
    st.info("Farmer Score와 RSI를 기반으로 조건 만족 시 자동으로 적립식 매수를 진행합니다.")
    
    st.write("### [미리보기] 매수 규칙 설정")
    target_symbol = st.selectbox("모으기 종목 선택", [s.symbol for s in db.query(Security).all()] if db.query(Security).first() else ["AAPL"])
    st.slider("기준 Farmer Score (이상일 때 매수)", 0, 100, 70, disabled=True)
    st.slider("기준 RSI (이하일 때 매수)", 0, 100, 40, disabled=True)
    qty = st.number_input("1회 매수 수량", min_value=0.1, value=1.0, step=0.1)
    
    if st.button("Toss API 연동 및 1회 주문 (Mock)"):
        try:
            payload = {
                "symbol": target_symbol,
                "side": "buy",
                "quantity": qty
            }
            resp = requests.post("http://localhost:8000/api/toss/order", json=payload)
            if resp.status_code == 200:
                st.success(f"Mock 주문 성공! {resp.json()}")
            else:
                st.error("주문 실패")
        except Exception as e:
            st.error(f"주문 요청 중 오류 발생: {e}")
