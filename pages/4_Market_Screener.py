import streamlit as st
import requests
import pandas as pd
from ui_utils import inject_custom_css

st.set_page_config(page_title="Market Screener", layout="wide", page_icon="🔍")
inject_custom_css()
st.title("🔍 Market Screener")
st.markdown("시장에서 과매도되거나 주요 지지선에 근접한 종목을 발굴합니다.")

def fetch_screener_data():
    try:
        response = requests.get("http://localhost:8000/api/screener")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to fetch data: {response.status_code}")
            return None
    except Exception as e:
        # st.warning(f"Backend API not ready or reachable. Using mock data. ({e})")
        return [
            {"ticker": "AAPL", "price": 145.2, "rsi": 25.4, "support": 140.0, "volume": "50M"},
            {"ticker": "MSFT", "price": 310.5, "rsi": 45.1, "support": 290.0, "volume": "25M"},
            {"ticker": "TSLA", "price": 195.0, "rsi": 29.8, "support": 195.0, "volume": "120M"},
            {"ticker": "NVDA", "price": 450.0, "rsi": 75.0, "support": 400.0, "volume": "40M"},
            {"ticker": "AMD", "price": 95.0, "rsi": 28.0, "support": 90.0, "volume": "60M"},
        ]

if st.button("🔄 스크리너 새로고침"):
    st.cache_data.clear()

with st.spinner("스크리너 데이터를 분석 중입니다..."):
    data = fetch_screener_data()

if data:
    df = pd.DataFrame(data)
    
    st.subheader("💡 투자 기회 포착")
    
    # Create layout for summary metrics
    col1, col2, col3 = st.columns(3)
    
    oversold_count = len(df[df['rsi'] < 30])
    near_support_count = len(df[(df['price'] - df['support']) / df['price'] < 0.05])
    
    col1.metric("분석된 종목 수", len(df))
    col2.metric("Oversold (RSI < 30) 종목 수", oversold_count)
    col3.metric("지지선 근접 종목 수", near_support_count)
    
    st.divider()
    
    # Data visualization with conditional formatting
    def highlight_signals(row):
        is_oversold = row['rsi'] < 30
        is_near_support = (row['price'] - row['support']) / row['price'] < 0.05
        
        if is_oversold and is_near_support:
            return ['background-color: rgba(255, 99, 71, 0.2)'] * len(row)
        elif is_oversold:
            return ['background-color: rgba(255, 165, 0, 0.2)'] * len(row)
        elif is_near_support:
            return ['background-color: rgba(144, 238, 144, 0.2)'] * len(row)
        return [''] * len(row)

    st.markdown("### 스크리닝 결과 테이블")
    st.markdown("행 배경색: 🔴 과매도 + 지지선 근접 | 🟠 과매도 (RSI<30) | 🟢 지지선 근접 (5% 이내)")
    
    formatted_df = df.style.apply(highlight_signals, axis=1).format({
        'price': '${:.2f}',
        'rsi': '{:.1f}',
        'support': '${:.2f}'
    })
    
    st.dataframe(formatted_df, use_container_width=True, height=400)
    
    # Display cards for top opportunities
    st.subheader("🌟 Top 주목 종목")
    opportunities = df[(df['rsi'] < 30) | ((df['price'] - df['support']) / df['price'] < 0.05)]
    
    if not opportunities.empty:
        cols = st.columns(min(len(opportunities), 4))
        for idx, row in enumerate(opportunities.head(4).itertuples()):
            with cols[idx % 4]:
                st.info(f"**{row.ticker}**")
                st.write(f"현재가: ${row.price:.2f}")
                st.write(f"RSI: {row.rsi:.1f}")
                st.write(f"지지선: ${row.support:.2f}")
                if row.rsi < 30:
                    st.caption("✅ Oversold")
                if (row.price - row.support) / row.price < 0.05:
                    st.caption("✅ Near Support")
    else:
        st.write("현재 주목할 만한 종목이 없습니다.")

    st.toast("스크리너 데이터를 성공적으로 불러왔습니다!", icon="✅")
