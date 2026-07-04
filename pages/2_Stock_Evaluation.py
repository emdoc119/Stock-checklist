import streamlit as st
import yfinance as yf
from database import get_db
from models import Security, SecurityEvaluation
import plotly.graph_objects as go
from datetime import date

st.set_page_config(page_title="Stock Evaluation", layout="wide")
st.title("🌱 종목 평가 (Farmer Score)")

db = next(get_db())
securities = db.query(Security).all()
symbols = [s.symbol for s in securities]

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("종목 선택")
    selected_symbol = st.selectbox("종목 (Symbol)", symbols + ["직접 입력..."])
    if selected_symbol == "직접 입력...":
        new_symbol = st.text_input("새로운 종목 심볼 입력 (예: TSLA, 000660.KS)").upper()
        if st.button("종목 추가") and new_symbol:
            new_sec = Security(symbol=new_symbol, name=new_symbol, country="US" if ".KS" not in new_symbol else "KR")
            db.add(new_sec)
            db.commit()
            st.success("종목 추가 완료! 새로고침 해주세요.")
            st.stop()
        selected_symbol = new_symbol
        
    security = db.query(Security).filter(Security.symbol == selected_symbol).first()

if security:
    with col2:
        st.subheader("농부식 정성/정량 평가 입력")
        
        evaluation = db.query(SecurityEvaluation).filter(SecurityEvaluation.security_id == security.id).first()
        if not evaluation:
            evaluation = SecurityEvaluation(security_id=security.id, evaluation_date=date.today())
            db.add(evaluation)
            db.commit()

        # Update Form
        with st.form("evaluation_form"):
            st.write("1점(매우 낮음) ~ 5점(매우 높음) 기준으로 평가하세요.")
            
            c1, c2 = st.columns(2)
            with c1:
                sg = st.slider("구조적 성장성 (EPS, 매출의 추세적 상승)", 1, 5, evaluation.structural_growth_score)
                bs = st.slider("시대의 병목 지위 (대체 불가능성, 수주잔고)", 1, 5, evaluation.bottleneck_score)
                vs = st.slider("밸류에이션 부담 (낮을수록 고득점)", 1, 5, evaluation.valuation_score)
            with c2:
                fs = st.slider("재무 안전성 (현금 흐름, 부채)", 1, 5, evaluation.financial_safety_score)
                ms = st.slider("모멘텀 (가격 추세, 거래량 바닥 확인 여부)", 1, 5, evaluation.momentum_score)
                ss = st.slider("시장 심리 (과도한 공포일 때 고득점)", 1, 5, evaluation.sentiment_score)
                
            thesis = st.text_area("투자 핵심 가설 및 코멘트", evaluation.thesis_text or "")
            
            submit = st.form_submit_button("평가 저장 및 업데이트")
            
            if submit:
                evaluation.structural_growth_score = sg
                evaluation.bottleneck_score = bs
                evaluation.valuation_score = vs
                evaluation.financial_safety_score = fs
                evaluation.momentum_score = ms
                evaluation.sentiment_score = ss
                evaluation.thesis_text = thesis
                
                # Farmer score is average of the 6 components, scaled to 100
                total = (sg + bs + vs + fs + ms + ss) / 30.0 * 100
                evaluation.farmer_score = total
                evaluation.evaluation_date = date.today()
                
                db.commit()
                st.success(f"평가 저장 완료! 종합 점수: {total:.1f}점")

    # Show radar chart
    st.markdown("---")
    st.subheader(f"{security.symbol} - Farmer Score Analysis")
    
    categories = ['구조적 성장성', '시대의 병목', '밸류에이션', '재무 안전성', '모멘텀', '시장 심리']
    values = [
        evaluation.structural_growth_score,
        evaluation.bottleneck_score,
        evaluation.valuation_score,
        evaluation.financial_safety_score,
        evaluation.momentum_score,
        evaluation.sentiment_score
    ]
    
    fig = go.Figure(data=go.Scatterpolar(
      r=values + [values[0]],
      theta=categories + [categories[0]],
      fill='toself',
      name='Farmer Score'
    ))

    fig.update_layout(
      polar=dict(
        radialaxis=dict(
          visible=True,
          range=[0, 5]
        )),
      showlegend=False,
      title=f"종합 농부 스코어: {evaluation.farmer_score:.1f} / 100"
    )
    
    st.plotly_chart(fig, use_container_width=True)
