import streamlit as st
import os

st.set_page_config(page_title="Farmer OS", layout="wide", page_icon="🌾")

from ui_utils import inject_custom_css
inject_custom_css()

st.title("🌾 Farmer OS (농부의 투자 철학)")
st.write("왼쪽 사이드바에서 메뉴를 선택하세요.")

st.markdown("""
### 투자 3원칙 리마인드
1. **사이클의 위치 파악**: 과열의 끝인가, 공포의 바닥인가?
2. **구조적 성장성 검토**: 시대의 병목을 장악한 기업인가?
3. **손실은 내 책임, 수익은 시장의 선물**: 자족하고 겸손하라.
""")
