import streamlit as st

def inject_custom_css():
    st.markdown("""
    <style>
    /* Dark mode aesthetic */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Remove default Streamlit top padding and block paddings */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Metric containers and cards rounded corners and subtle shadows */
    [data-testid="stMetric"] {
        background-color: #1a1c24 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.5) !important;
        border: 1px solid #2d303a;
    }
    
    /* Metric up/down arrows to neon green/red */
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Up"] {
        color: #39ff14 !important; /* Neon green */
        fill: #39ff14 !important;
    }
    [data-testid="stMetricDelta"] svg[data-testid="stMetricDeltaIcon-Down"] {
        color: #ff073a !important; /* Neon red */
        fill: #ff073a !important;
    }
    
    /* Change delta text color using standard sibling / parent structures if possible, 
       but standard Streamlit inline styles might override. Using :has for modern browsers */
    div[data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Up"]) > div {
        color: #39ff14 !important;
    }
    div[data-testid="stMetricDelta"]:has(svg[data-testid="stMetricDeltaIcon-Down"]) > div {
        color: #ff073a !important;
    }
    
    /* Headers to look more like a terminal */
    h1, h2, h3 {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)
