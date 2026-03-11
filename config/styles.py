import streamlit as st

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #0E1117;
    border-right: 1px solid #262730;
}

/* GLASS CARDS */
.glass-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    color: white;
}

/* FEATURE CARDS (HOME) */
.feature-box {
    background: #1e1e1e;
    border-radius: 15px;
    padding: 20px;
    text-align: center;
    border: 1px solid #333;
    transition: transform 0.3s;
}
.feature-box:hover {
    transform: scale(1.05);
    border-color: #00E676;
}

/* FUN METRICS */
div[data-testid="stMetricValue"] {
    background: -webkit-linear-gradient(45deg, #FFEB3B, #00E676);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}

/* BUTTONS */
.stButton>button {
    background: linear-gradient(90deg, #FF512F 0%, #DD2476 100%);
    color: white;
    border-radius: 12px;
    border: none;
    height: 50px;
    font-weight: 600;
    transition: 0.2s;
}
.stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(221, 36, 118, 0.4); }
</style>
"""


def inject_css():
    st.markdown(APP_CSS, unsafe_allow_html=True)
