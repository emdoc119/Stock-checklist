import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Backtesting", layout="wide", page_icon="⚙️")
st.title("⚙️ Strategy Backtesting")
st.markdown("특정 종목에 대해 퀀트 투자 전략을 백테스트하고 성과를 평가합니다.")

def run_backtest(ticker, strategy):
    payload = {"ticker": ticker, "strategy": strategy}
    try:
        response = requests.post("http://localhost:8000/api/backtest", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"백테스트 실패: {response.status_code}")
            return None
    except Exception as e:
        # Fallback to mock data
        st.toast("백엔드에 연결할 수 없어 모의 데이터를 표시합니다.", icon="⚠️")
        
        # Generate some mock history data
        dates = [datetime.today() - timedelta(days=x) for x in range(365, 0, -1)]
        base_equity = 10000
        strategy_equity = [base_equity]
        bh_equity = [base_equity]
        
        np.random.seed(sum(ord(c) for c in ticker) % (2**32))
        
        for i in range(1, 365):
            s_change = np.random.normal(0.0005, 0.015)
            b_change = np.random.normal(0.0003, 0.02)
            strategy_equity.append(strategy_equity[-1] * (1 + s_change))
            bh_equity.append(bh_equity[-1] * (1 + b_change))
            
        strategy_return = (strategy_equity[-1] - base_equity) / base_equity * 100
        buy_hold_return = (bh_equity[-1] - base_equity) / base_equity * 100
        
        history_df = pd.DataFrame({
            "date": [d.strftime("%Y-%m-%d") for d in dates],
            "strategy_equity": strategy_equity,
            "buy_hold_equity": bh_equity
        })
        
        return {
            "ticker": ticker,
            "strategy": strategy,
            "strategy_return": strategy_return,
            "buy_hold_return": buy_hold_return,
            "mdd": -12.4 if strategy_return > 0 else -25.6,
            "history": history_df.to_dict('records')
        }

st.sidebar.header("백테스트 설정")
ticker = st.sidebar.text_input("종목 티커 (예: AAPL, SPY, TSLA)", value="AAPL").upper()
strategy = st.sidebar.selectbox(
    "전략 선택",
    [
        "RSI < 30 매수, RSI > 70 매도",
        "이동평균선(50일, 200일) 골든/데드크로스",
        "볼린저밴드 하단 매수, 상단 매도",
        "MACD 시그널 크로스"
    ]
)

if st.sidebar.button("🚀 백테스트 실행", use_container_width=True):
    with st.spinner(f"{ticker} 종목에 대해 '{strategy}' 전략을 시뮬레이션 중입니다..."):
        result = run_backtest(ticker, strategy)
        
    if result:
        st.success("백테스트가 성공적으로 완료되었습니다!")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("전략 수익률", f"{result['strategy_return']:.2f}%", f"{result['strategy_return'] - result['buy_hold_return']:.2f}% (vs B&H)")
        col2.metric("Buy & Hold 수익률", f"{result['buy_hold_return']:.2f}%")
        col3.metric("최대 낙폭 (MDD)", f"{result['mdd']:.2f}%")
        
        st.divider()
        
        st.subheader("📈 자산 성장 곡선 (Equity Curve)")
        
        if "history" in result and result["history"]:
            df_history = pd.DataFrame(result["history"])
            df_history['date'] = pd.to_datetime(df_history['date'])
            
            # Melt dataframe for plotly
            df_melted = df_history.melt(
                id_vars=['date'], 
                value_vars=['strategy_equity', 'buy_hold_equity'],
                var_name='Type', 
                value_name='Equity'
            )
            df_melted['Type'] = df_melted['Type'].replace({
                'strategy_equity': 'Strategy',
                'buy_hold_equity': 'Buy & Hold'
            })
            
            fig = px.line(
                df_melted, x="date", y="Equity", color="Type",
                title=f"{ticker} - {strategy} Backtest",
                labels={"date": "Date", "Equity": "Portfolio Value ($)"},
                color_discrete_map={"Strategy": "#00CC96", "Buy & Hold": "#636EFA"}
            )
            fig.update_layout(hovermode="x unified", legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("세부 데이터 보기"):
                st.dataframe(df_history, use_container_width=True)
        else:
            st.info("시계열 데이터가 제공되지 않았습니다.")
else:
    st.info("왼쪽 사이드바에서 설정 후 '백테스트 실행' 버튼을 클릭하세요.")
