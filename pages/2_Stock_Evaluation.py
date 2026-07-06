import streamlit as st
import yfinance as yf
import requests
from database import get_db
from models import Security, SecurityEvaluation
import plotly.graph_objects as go
from datetime import date
from ui_utils import inject_custom_css

st.set_page_config(page_title="Stock Evaluation", layout="wide")
inject_custom_css()
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
        st.subheader("기술적 지표 (RSI)")
        with st.spinner('데이터를 불러오는 중입니다...'):
            try:
                resp = requests.get(f"http://localhost:8000/api/indicators/{security.symbol}")
                if resp.status_code == 200:
                    rsi = resp.json().get("rsi_14", 50.0)
                    st.metric("RSI (14일)", f"{rsi:.1f}", help="RSI 30 이하는 과매도(매수 추천), 70 이상은 과매수(매도 추천) 구간으로 해석됩니다.")
                    if rsi < 30:
                        st.success("✅ 과매도 (RSI < 30) - 씨앗 뿌리기 구간")
                    elif rsi > 70:
                        st.warning("⚠️ 과매수 (RSI > 70) - 수확 구간")
                    else:
                        st.info("➖ 중립 구간")
            except Exception:
                st.write("지표를 불러올 수 없습니다.")
                
        st.subheader("종목 차트 (최근 6개월)")
        with st.spinner('차트 데이터를 불러오는 중입니다...'):
            try:
                ticker = yf.Ticker(security.symbol)
                hist = ticker.history(period="6mo")
                if not hist.empty:
                    # Calculate MAs
                    hist['MA5'] = hist['Close'].rolling(window=5).mean()
                    hist['MA20'] = hist['Close'].rolling(window=20).mean()
                    hist['MA60'] = hist['Close'].rolling(window=60).mean()
                    hist['MA120'] = hist['Close'].rolling(window=120).mean()
                    
                    fig_chart = go.Figure(data=[go.Candlestick(x=hist.index,
                                    open=hist['Open'],
                                    high=hist['High'],
                                    low=hist['Low'],
                                    close=hist['Close'],
                                    increasing=dict(line=dict(color='#00ff00'), fillcolor='#00ff00'),
                                    decreasing=dict(line=dict(color='#ff073a'), fillcolor='#ff073a'),
                                    name='Candlestick')])
                                    
                    fig_chart.add_trace(go.Scatter(x=hist.index, y=hist['MA5'], mode='lines', name='5일선', line=dict(color='#1f77b4', width=1)))
                    fig_chart.add_trace(go.Scatter(x=hist.index, y=hist['MA20'], mode='lines', name='20일선', line=dict(color='#ff7f0e', width=1)))
                    fig_chart.add_trace(go.Scatter(x=hist.index, y=hist['MA60'], mode='lines', name='60일선', line=dict(color='#2ca02c', width=1)))
                    fig_chart.add_trace(go.Scatter(x=hist.index, y=hist['MA120'], mode='lines', name='120일선', line=dict(color='#9467bd', width=1)))
                    
                    fig_chart.update_layout(
                        template="plotly_dark",
                        xaxis_rangeslider_visible=False,
                        title=f"{security.symbol} 일봉 차트",
                        margin=dict(t=30, b=0, l=0, r=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=False)
                    )
                    st.plotly_chart(fig_chart, use_container_width=True)
                else:
                    st.info("차트 데이터가 없습니다.")
            except Exception as e:
                st.error("차트를 불러오는 중 오류가 발생했습니다.")
            
        st.divider()
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
                st.toast(f"평가 저장 완료! 종합 점수: {total:.1f}점", icon="✅")
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
      template="plotly_dark",
      polar=dict(
        radialaxis=dict(
          visible=True,
          range=[0, 5]
        )),
      showlegend=False,
      title=f"종합 농부 스코어: {evaluation.farmer_score:.1f} / 100"
    )
    
    st.plotly_chart(fig, use_container_width=True)
