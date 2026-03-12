import streamlit as st

APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }

/* HIDE DEFAULT SIDEBAR ON AUTH */
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

/* ─── ONBOARDING ─── */
.onboarding-container {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem 1rem;
}
.onboarding-header {
    text-align: center;
    margin-bottom: 2rem;
}
.onboarding-header h1 { color: #00E676; font-size: 2.5rem; margin-bottom: 0.2rem; }
.onboarding-header p { color: #bbb; font-size: 1rem; }

.step-progress {
    display: flex;
    justify-content: center;
    gap: 8px;
    margin-bottom: 2rem;
}
.step-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    background: #333;
    transition: all 0.3s;
}
.step-dot.active { background: #00E676; transform: scale(1.3); }
.step-dot.done { background: #00E676; opacity: 0.5; }

.step-label {
    text-align: center;
    color: #00E676;
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    letter-spacing: 0.5px;
}
.step-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}
.step-emoji { font-size: 2.5rem; text-align: center; margin-bottom: 0.5rem; }
.step-title { text-align: center; font-size: 1.5rem; font-weight: 700; color: #fff; margin-bottom: 0.3rem; }
.step-subtitle { text-align: center; color: #aaa; font-size: 0.95rem; margin-bottom: 1.5rem; }

/* ─── TOP NAV BAR ─── */
.topnav {
    display: flex;
    justify-content: center;
    gap: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 6px;
    margin-bottom: 1.5rem;
    max-width: 700px;
    margin-left: auto;
    margin-right: auto;
}
.topnav-item {
    flex: 1;
    text-align: center;
    padding: 10px 8px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s;
    color: #888;
    font-size: 0.85rem;
    font-weight: 600;
    text-decoration: none;
}
.topnav-item:hover { background: rgba(255,255,255,0.06); color: #fff; }
.topnav-item.active {
    background: linear-gradient(90deg, #FF512F, #DD2476);
    color: #fff;
    box-shadow: 0 4px 15px rgba(221, 36, 118, 0.3);
}
.topnav-icon { font-size: 1.3rem; display: block; margin-bottom: 2px; }

/* ─── SMART LOG BAR ─── */
.smart-log-bar {
    background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
}

/* ─── GOAL PROGRESS ─── */
.goal-progress-container {
    background: linear-gradient(135deg, rgba(0,230,118,0.08), rgba(0,230,118,0.02));
    border: 1px solid rgba(0,230,118,0.15);
    border-radius: 20px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.5rem;
}
.progress-bar-outer {
    background: rgba(255,255,255,0.08);
    border-radius: 12px;
    height: 24px;
    overflow: hidden;
    margin: 8px 0;
}
.progress-bar-fill {
    height: 100%;
    border-radius: 12px;
    transition: width 0.5s ease;
    background: linear-gradient(90deg, #00E676, #00BCD4);
}
.progress-bar-fill.warn {
    background: linear-gradient(90deg, #FF9800, #FF5722);
}
.progress-bar-fill.over {
    background: linear-gradient(90deg, #F44336, #D32F2F);
}

/* ─── TODAY CARDS ─── */
.today-card {
    background: linear-gradient(135deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    transition: transform 0.2s;
    height: 100%;
}
.today-card:hover { transform: translateY(-3px); border-color: rgba(0,230,118,0.3); }
.today-card-icon { font-size: 2rem; margin-bottom: 0.3rem; }
.today-card-label { color: #888; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
.today-card-value { color: #fff; font-size: 1.8rem; font-weight: 800; }
.today-card-sub { color: #aaa; font-size: 0.8rem; }

/* ─── AI RECOMMENDATION CARD ─── */
.ai-card {
    background: linear-gradient(135deg, rgba(103,58,183,0.15), rgba(33,150,243,0.1));
    border: 1px solid rgba(103,58,183,0.2);
    border-radius: 16px;
    padding: 1.2rem;
    margin-bottom: 0.8rem;
}
.ai-card-title { font-weight: 700; color: #BB86FC; margin-bottom: 0.3rem; }
.ai-card-text { color: #ccc; font-size: 0.9rem; }

/* ─── SECTION HEADER ─── */
.section-header {
    font-size: 1.1rem;
    font-weight: 700;
    color: #fff;
    margin: 1.5rem 0 0.8rem 0;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
</style>
"""


def inject_css():
    st.markdown(APP_CSS, unsafe_allow_html=True)
