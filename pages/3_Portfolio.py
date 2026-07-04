import streamlit as st
import pandas as pd
import plotly.express as px
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
