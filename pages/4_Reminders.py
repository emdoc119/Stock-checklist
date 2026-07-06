import streamlit as st
import pandas as pd
from database import get_db
from models import TradeJournal, Security
from ui_utils import inject_custom_css

st.set_page_config(page_title="Reminders & Journal", layout="wide")
inject_custom_css()
st.title("📝 Reminders & Journal")

db = next(get_db())

col1, col2 = st.columns(2)

with col1:
    st.subheader("매수/매도 전 리마인드 (체크리스트)")
    
    with st.form("trade_journal_form"):
        securities = db.query(Security).all()
        symbols = [s.symbol for s in securities]
        symbol = st.selectbox("종목 선택", symbols)
        
        side = st.radio("포지션", ["BUY", "SELL"])
        
        st.write("---")
        st.write("**[농부의 3원칙 체크]**")
        q1 = st.checkbox("지금은 과열의 끝이 아니라 공포의 바닥입니까?")
        q2 = st.checkbox("단순 내러티브가 아닌 실적/병목 지위가 증명된 기업입니까?")
        q3 = st.checkbox("손실은 내 책임, 수익은 시장의 선물이라는 것을 받아들입니까?")
        
        st.write("---")
        hypothesis = st.text_area("투자 가설 및 출구 전략 (진입 이유/손절 조건/익절 목표)")
        
        submit = st.form_submit_button("저널 기록 및 매매 허가 검토")
        
        if submit:
            passed = q1 and q2 and q3
            journal = TradeJournal(
                symbol=symbol,
                side=side,
                hypothesis_text=hypothesis,
                checklist_passed=passed
            )
            db.add(journal)
            db.commit()
            
            if passed:
                st.success("✅ 농부 철학 체크리스트를 모두 통과했습니다. 냉정하게 매매를 진행하셔도 좋습니다.")
            else:
                st.error("🚫 원칙을 모두 지키지 못했습니다! 조급한 감정적 매매가 아닌지 다시 한 번 생각해보세요.")
                
with col2:
    st.subheader("최근 거래 저널")
    journals = db.query(TradeJournal).order_by(TradeJournal.created_at.desc()).limit(10).all()
    
    if journals:
        data = []
        for j in journals:
            data.append({
                "시간": j.created_at.strftime("%Y-%m-%d %H:%M"),
                "종목": j.symbol,
                "방향": j.side,
                "원칙 준수": "O" if j.checklist_passed else "X",
                "가설": j.hypothesis_text
            })
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("아직 작성된 저널이 없습니다.")
